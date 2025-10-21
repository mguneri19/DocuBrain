"""
RAG Chain modülü - Basit Retrieval-Augmented Generation

Bu modül şu görevleri yerine getirir:
- Hybrid Retriever ile doküman alma (BM25 + Vector + RRF + Reranker)
- LLM'e bağlam ile soru gönderme
- Dinamik prompt yönetimi (kısa/uzun cevap)
- Token kullanımı takibi
"""
from __future__ import annotations
from typing import List, Dict
from dataclasses import dataclass

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from config import SEARCH_TYPE, TOP_K, MMR_LAMBDA, DEFAULT_OPENAI_MODEL
from utils import format_docs_for_prompt, format_citations
# Hybrid retriever removed for simplicity

SYSTEM_PROMPT_SHORT = """
Sen bir kurumsal bilgi tabanı asistanısın. Verilen CONTEXT içindeki bilgilere dayanarak KISA ve ÖZ cevaplar ver.

ÖNEMLİ KURALLAR:
1. Cevabını MUTLAKA 2-3 cümle ile sınırla - uzun açıklamalar yapma
2. Sadece sorulan soruya direkt cevap ver, ek bilgi ekleme
3. CONTEXT'teki ilgili bilgileri özetle, detaylara girme
4. Eğer CONTEXT'te bilgi varsa ama doğrudan cevap yoksa, kısa özet ver
5. Sadece CONTEXT'te hiç ilgili bilgi yoksa "Bu soruyu yüklenen dokümanlarda bulamadım." de
6. Yanıtlarının sonunda kullandığın kaynakları [kaynak: dosya p.syf] formatında listele
7. Türkçe cevap ver ve kısa, net ol

KISA VE ÖZ CEVAP VER - UZUN AÇIKLAMALAR YAPMA!
""".strip()

SYSTEM_PROMPT_DETAILED = """
Sen bir kurumsal bilgi tabanı asistanısın. Verilen CONTEXT içindeki bilgilere dayanarak DETAYLI ve KAPSAMLI cevaplar ver.

ÖNEMLİ KURALLAR:
1. CONTEXT'teki tüm ilgili bilgileri birleştir ve kapsamlı cevap ver
2. Eğer CONTEXT'te bilgi varsa ama doğrudan cevap yoksa, ilgili bilgileri birleştirerek mantıklı sonuç çıkar
3. Detayları açıkla, örnekler ver, bağlam sağla
4. Sadece CONTEXT'te hiç ilgili bilgi yoksa "Bu soruyu yüklenen dokümanlarda bulamadım." de
5. Yanıtlarının sonunda kullandığın kaynakları [kaynak: dosya p.syf] formatında listele
6. Türkçe cevap ver ve açık, anlaşılır ol

DETAYLI VE KAPSAMLI CEVAP VER - TÜM İLGİLİ BİLGİLERİ BİRLEŞTİR!
""".strip()

def get_prompt_template(is_short=True):
    """
    Cevap stiline göre uygun prompt template'i döndürür.
    
    """
    system_prompt = SYSTEM_PROMPT_SHORT if is_short else SYSTEM_PROMPT_DETAILED
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Soru: {question}\n\nCONTEXT:\n{context}"),
        ]
    )

def build_retriever(vs: Chroma, search_type: str = SEARCH_TYPE, top_k: int = TOP_K, mmr_lambda: float = MMR_LAMBDA):
    """
    Basit retriever oluşturur - Vector search.
    
    """
    if search_type == "mmr":
        return vs.as_retriever(
            search_type="mmr",
            search_kwargs={"k": top_k, "fetch_k": max(50, top_k * 5), "lambda_mult": mmr_lambda},
        )
    return vs.as_retriever(search_kwargs={"k": top_k})

def answer_with_chain(llm, retriever, question: str, is_short: bool = True) -> Dict:
    """
    RAG Chain ile soru cevaplar (Retrieve + Generate).
    
    """
    from langchain_community.callbacks import get_openai_callback
    
    # Retrieve
    docs: List[Document] = retriever.invoke(question)
    context = format_docs_for_prompt(docs)
    
    # Generate with appropriate prompt - token tracking ile
    prompt_template = get_prompt_template(is_short)
    chain = prompt_template | llm | StrOutputParser()
    
    # Token kullanımını takip et
    with get_openai_callback() as cb:
        answer = chain.invoke({"question": question, "context": context})
        tokens_used = {
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_tokens": cb.total_tokens,
            "total_cost": cb.total_cost
        }
    
    cites = format_citations(docs)
    return {
        "answer": answer, 
        "docs": docs, 
        "citations": cites,
        "tokens": tokens_used
    }
