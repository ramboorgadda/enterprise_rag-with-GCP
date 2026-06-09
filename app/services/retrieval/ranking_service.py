import time
import logfire
from app.config import settings
from flashrank import Ranker,RerankRequest

_ranker = None
def _get_Ranker() -> Ranker:
    """Initializes the FlashRank engine lazily. 
    FlashRank uses a local ONNX model (ms-marco-MiniLM-L-6-v2) for ultra-fast reranking.
    """
    global _ranker
    if _ranker is None:
        logfire.info("🧠 Initializing FlashRank Model (TinyBERT) locally...")
        try:
            _ranker = Ranker(cache_dir="/tmp/flashrank")
        except Exception as e:
            _ranker = Ranker()   
    return _ranker

def rerank_documents(query: str, documents: list[dict], top_k: int = 5) ->list[str]:
    """
    Refines retrieval results by re-scoring documents against the query semantically.
    
    Why FlashRank? 
    Standard vector search (Cosine Similarity) is fast but mathematically "fuzzy."
    FlashRank uses a Cross-Encoder approach which is much more precise but usually slow.
    FlashRank solves this by using highly optimized, quantized ONNX models locally.
    """
    if not documents:
        return []
    start_time = time.time()
    logfire.info(f"📡 [Reranker] Sending {len(documents)} docs to FlashRank Cross-Encoder...")
    
    try:
        ranker = _get_Ranker()
        passages =[
            {"id": i, "text":doc} for i, doc in enumerate(documents)
        ]
        request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(request)
        reranked_docs = []
        for res in results[:top_k]:
            if isinstance(res, dict):
                passage = res.get("passage") or {}
                idx = passage.get("id")
                score = res.get("score", 0.0)
                text = passage.get("text")
            else:
                passage = getattr(res, "passage", None)
                idx = getattr(passage, "id", None)
                score = getattr(res, "score", 0.0)
                text = getattr(passage, "text", None)

            if text:
                reranked_docs.append(text)
                logfire.info(f"🔍 Reranked Doc ID {idx} with score {score:.4f}")

        if not reranked_docs:
            return documents[:top_k]
    except Exception as e:
        logfire.error(f"❌ Error during reranking: {e}")
        return documents[:top_k]
    end_time = time.time()
    logfire.info(f"⏱️ Reranking completed in {end_time - start_time:.2f} seconds")
    return reranked_docs