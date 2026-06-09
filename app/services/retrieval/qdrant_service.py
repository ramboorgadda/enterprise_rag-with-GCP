import logfire
from qdrant_client import QdrantClient
from app.config import settings
from app.services.retrieval.embedding import embed_query

client = QdrantClient(url=settings.QDRANT_URL, 
                    api_key=settings.QDRANT_API_KEY)

def search_enterprise_knowledge(query: str, top_k: int = 8):
    """Search the enterprise knowledge base using Qdrant.

    Args:
        query (str): The search query.
        top_k (int, optional): The number of top results to return. Defaults to 8.

    Returns:
        list: A list of search results.
    """
    try:
        query_vector = embed_query(query)
        response = client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )
        results = []
        points = getattr(response, "points", None)
        if points is None and getattr(response, "result", None) is not None:
            points = getattr(response.result, "points", [])
        if points is None:
            points = []

        for res in points:
            payload = getattr(res, "payload", {}) or {}
            results.append({
                "content": payload.get("text", ""),
                "source": payload.get("source", "Unknown"),
                "score": getattr(res, "score", 0.0)
            })
        return results
    except Exception as e:
        logfire.error(f"Error during Qdrant search: {e}")
        return []