import logfire
from app.agents.state import AgentState
from app.services.retrieval.qdrant_service import search_enterprise_knowledge
from app.services.retrieval.ranking_service import rerank_documents
from app.config import settings

def retrieve_node(state: AgentState):
    """
    Performs vector search and semantic reranking for technical queries.
    """
    query = state["current_query"]
    if query == "CONVERSATIONAL":
        logfire.info("Handling conversational query using memory only.")
        return {
            "final_answer": "",
            "status": "Conversational query - no retrieval needed.",
            "messages": []
        }
    else:
        logfire.info("Performing technical retrieval.")
        retrieved_docs = search_enterprise_knowledge(query, settings.RETRIEVAL_TOP_K)
        ranked_docs = rerank_documents(retrieved_docs, query, top_k=5)
        state["documents"] = ranked_docs
        formatted_doc = [f"CONTENT: {doc}" for doc in ranked_docs]
        return {
            "documents": formatted_doc,
            "status": "Technical retrieval completed.",
            "plan": state["plan"] + ["Context Retrieved"]
        }