"""
Agent modülü - Tool-calling ile gelişmiş RAG

Bu modül şu görevleri yerine getirir:
- LangChain Agent oluşturur (tool-calling destekli LLM gerektirir)
- Retriever'ı bir "tool" olarak sunar (kb_search)
- Agent otomatik olarak ne zaman retrieval yapacağına karar verir
- Token kullanımı takibi
- Dinamik prompt yönetimi (kısa/uzun cevap)
"""
from __future__ import annotations
from typing import Dict, List, Any

from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import create_retriever_tool
from langchain_openai import ChatOpenAI

from config import DEFAULT_OPENAI_MODEL
from utils import format_citations

AGENT_SYSTEM_SHORT = """
Sen bir kurumsal bilgi tabanı ajanısın. SORU'ları yanıtlarken **daima** 'kb_search' aracını kullan.
Yalnızca bu araçtan gelen belgeleri kanıt olarak kabul et ve kanıt yetersizse bunu açıkça belirt.

ÖNEMLİ: Cevabını MUTLAKA 2-3 cümle ile sınırla. KISA VE ÖZ cevap ver!
""".strip()

AGENT_SYSTEM_DETAILED = """
Sen bir kurumsal bilgi tabanı ajanısın. SORU'ları yanıtlarken **daima** 'kb_search' aracını kullan.
Yalnızca bu araçtan gelen belgeleri kanıt olarak kabul et ve kanıt yetersizse bunu açıkça belirt.

ÖNEMLİ: DETAYLI ve KAPSAMLI cevap ver. Tüm ilgili bilgileri birleştir ve açıkla.
""".strip()

def _resolve_agent_executor_class() -> Any:
    """
    LangChain versiyonuna göre AgentExecutor sınıfını bulur.
    
    """
    try:
        from langchain.agents import AgentExecutor as _AE  # type: ignore
        return _AE
    except Exception:
        try:
            from langchain.agents.agent import AgentExecutor as _AE  # type: ignore
            return _AE
        except Exception:
            try:
                from langchain_core.agents import AgentExecutor as _AE  # type: ignore
                return _AE
            except Exception:
                try:
                    from langchain.agents.executor import AgentExecutor as _AE  # type: ignore
                    return _AE
                except Exception as e:
                    raise ImportError(
                        "AgentExecutor bulunamadı. LangChain sürümü ile uyumsuzluk var. "
                        "Lütfen 'pip install \"langchain>=0.2.16,<0.3\"' komutuyla güncelleyin."
                    ) from e


def build_agent(llm: ChatOpenAI, retriever, is_short: bool = True) -> Any:
    """
    LangChain Agent oluşturur (tool-calling ile).
    
    """
    # LangChain 1.0+ için agent yapısı - create_agent kullan
    try:
        from langchain.agents import create_agent as _create_tool_calling_agent  # type: ignore
    except Exception as e:
        raise ImportError(
            "create_agent bulunamadı. LangChain sürümü ile uyumsuzluk var. "
            "Lütfen 'pip install \"langchain>=1.0.0\"' komutuyla güncelleyin."
        ) from e
    # Tool: retriever as a tool, return docs for citations
    kb_tool = create_retriever_tool(
        retriever=retriever,
        name="kb_search",
        description=(
            "Kurumsal bilgi tabanında (PDF/DOCX) semantik arama yapar ve ilgili parçaları döndürür. "
            "Her soru için önce bu aracı kullan ve kanıtlara dayalı cevap ver."
        ),
    )

    # Cevap stiline göre system prompt seç
    system_prompt = AGENT_SYSTEM_SHORT if is_short else AGENT_SYSTEM_DETAILED
    
    # LangChain 1.0+ create_agent kullanımı: model (llm yerine), tools, system_prompt
    agent = _create_tool_calling_agent(
        model=llm,  # 'llm' yerine 'model' parametresi
        tools=[kb_tool],
        system_prompt=system_prompt
    )
    
    # Agent artık CompiledStateGraph döndürüyor, doğrudan kullanılabilir
    return agent

def run_agent(executor: Any, question: str, chat_history: List) -> Dict:
    """
    Agent'i çalıştırır ve soru cevaplar.
    
    """
    # LangChain 1.0+ create_agent: invoke ile {"messages": []} formatı kullanır
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_community.callbacks import get_openai_callback
    
    messages = []
    for msg in chat_history:
        messages.append(msg)
    
    # Son soruyu ekle
    messages.append(HumanMessage(content=question))
    
    # Agent'i çalıştır - token tracking ile
    with get_openai_callback() as cb:
        result = executor.invoke({"messages": messages})
        tokens_used = {
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_tokens": cb.total_tokens,
            "total_cost": cb.total_cost
        }
    
    # Cevabı al - LangChain 1.0+ 'messages' listesinin son elemanı cevaptır
    answer = ""
    if "messages" in result and result["messages"]:
        last_message = result["messages"][-1]
        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # TODO: Citations için tool çağrılarını topla (şu an basit versiyon)
    docs = []
    cites = ""
    return {
        "answer": answer, 
        "docs": docs, 
        "citations": cites, 
        "raw": result,
        "tokens": tokens_used
    }
