"""
Hybrid Retriever: BM25 (lexical) + Vector (semantic) + RRF + Reranker
"""
from __future__ import annotations
from typing import List, Dict, Any
import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from config import PERSIST_DIRECTORY


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever combining:
    1. BM25 (lexical search)
    2. Vector similarity (semantic search)
    3. RRF (Reciprocal Rank Fusion)
    4. Cross-encoder reranking
    """
    
    vectorstore: Any = None
    bm25: Any = None
    corpus_docs: List[Document] = []
    top_k: int = 8
    rerank_top_n: int = 8  # RRF'den sonra kaç tane rerank edilecek
    final_top_k: int = 5  # Son olarak kaç tane döndürülecek
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    class Config:
        arbitrary_types_allowed = True
        # Allow extra fields for internal state
        extra = "allow"
    
    def _get_reranker(self) -> CrossEncoder:
        """
        Cross-encoder reranker modelini yükler (lazy loading).
        
        """
        if not hasattr(self, '_reranker_cache'):
            self._reranker_cache = {}
        
        if 'reranker' not in self._reranker_cache:
            self._reranker_cache['reranker'] = CrossEncoder(self.reranker_model, device='cpu')
        
        return self._reranker_cache['reranker']
    
    def _reciprocal_rank_fusion(
        self, 
        bm25_results: List[Document],
        vector_results: List[Document],
        k: int = 60
    ) -> List[Document]:
        """
        Reciprocal Rank Fusion (RRF) ile iki sıralamayı birleştirir.
        
        """
        # Create score dict
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        
        # BM25 scores
        for rank, doc in enumerate(bm25_results, start=1):
            doc_id = doc.page_content[:100]  # Use first 100 chars as ID
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
            doc_map[doc_id] = doc
        
        # Vector scores
        for rank, doc in enumerate(vector_results, start=1):
            doc_id = doc.page_content[:100]
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
            doc_map[doc_id] = doc
        
        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top documents
        return [doc_map[doc_id] for doc_id, _ in sorted_docs[:self.rerank_top_n]]
    
    def _rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """
        Cross-encoder ile dokümanları yeniden sıralar (reranking).
        
        """
        if not documents:
            return documents
        
        reranker = self._get_reranker()
        
        # Prepare pairs for cross-encoder
        pairs = [[query, doc.page_content] for doc in documents]
        
        # Get scores
        scores = reranker.predict(pairs)
        
        # Sort by score
        doc_score_pairs = list(zip(documents, scores))
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top documents
        return [doc for doc, _ in doc_score_pairs[:self.final_top_k]]
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """
        Main retrieval logic:
        1. BM25 search (lexical)
        2. Vector search (semantic)
        3. RRF fusion
        4. Cross-encoder reranking
        """
        # 1. BM25 search
        bm25_results = []
        if self.bm25 and self.corpus_docs:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
            # Get top-k indices
            top_indices = sorted(
                range(len(bm25_scores)), 
                key=lambda i: bm25_scores[i], 
                reverse=True
            )[:self.top_k]
            bm25_results = [self.corpus_docs[i] for i in top_indices]
        
        # 2. Vector search
        vector_results = []
        if self.vectorstore:
            vector_results = self.vectorstore.similarity_search(query, k=self.top_k)
        
        # 3. RRF fusion
        fused_results = self._reciprocal_rank_fusion(bm25_results, vector_results)
        
        # 4. Reranking
        reranked_results = self._rerank(query, fused_results)
        
        return reranked_results


def build_bm25_index(documents: List[Document]) -> BM25Okapi:
    """
    Dokümanlardan BM25 index'i oluşturur.
    
    """
    # Tokenize corpus
    tokenized_corpus = [doc.page_content.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


def save_bm25_index(bm25: BM25Okapi, documents: List[Document], path: Path = None):
    """
    BM25 index ve dokümanları diske kaydeder.
    
    """
    if path is None:
        path = PERSIST_DIRECTORY / "bm25_index.pkl"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'wb') as f:
        pickle.dump({'bm25': bm25, 'documents': documents}, f)


def load_bm25_index(path: Path = None) -> tuple[BM25Okapi, List[Document]]:
    """
    
    """
    if path is None:
        path = PERSIST_DIRECTORY / "bm25_index.pkl"
    
    if not path.exists():
        return None, []
    
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    return data['bm25'], data['documents']


def build_hybrid_retriever(
    vectorstore,
    top_k: int = 8,
    rerank_top_n: int = 8,
    final_top_k: int = 5,
) -> HybridRetriever:
    """
    Build hybrid retriever with BM25 + Vector + RRF + Reranker
    """
    # Load BM25 index
    bm25, corpus_docs = load_bm25_index()
    
    return HybridRetriever(
        vectorstore=vectorstore,
        bm25=bm25,
        corpus_docs=corpus_docs,
        top_k=top_k,
        rerank_top_n=rerank_top_n,
        final_top_k=final_top_k,
    )

