import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings
from app.services.retrieval.embedding import get_embedding_model,embed_query

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
        response =client.query_points(collection_name=settings.QDRANT_COLLECTION,
                            query_vector=query_vector,
                            limit=top_k,
                            with_payload=True)
        results = []
        for res in response.results.points:
            payload = res.payload
            results.append({
                "content": payload.get("text", ""),
                "source": payload.get("source", "Unknown"),
                "score": res.score
            })
        return results
    except Exception as e:
        logfire.error(f"Error during Qdrant search: {e}")
        return []