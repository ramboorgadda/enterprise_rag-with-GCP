"""
Semantic cache backed by Redis (Google Memorystore).

How it works:
1. Embed the user query with Vertex AI (same model used for Qdrant search).
2. Scan cached entries and compute cosine distance in numpy.
3. If any stored query is within DISTANCE_THRESHOLD, return its cached answer.
4. On a new answer, store query + embedding + answer with a TTL.

Scale note: linear scan is fine up to ~10k cached entries. For larger caches,
switch to redisvl with a FLAT or HNSW vector index.
"""
import os

from app.config import settings
import logfire
from redisvl.extensions.cache.llm import SemanticCache
from redisvl.utils.vectorize.text.vertexai import VertexAITextVectorizer

DISTANCE_THRESHOLD = float(os.getenv("CACHE_DISTANCE_THRESHOLD", "0.15"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
KEY_PREFIX = "sem_cache:"

_cache = None

def init_cache():
    """
    Returns a Redis client connected to the configured host and port.
    """
    global _cache
    if settings.LOCAL_MODE or not settings.REDIS_HOST:
        logfire.warning("⚠️ Redis Cache disabled (Local Mode or Missing Host)")
        return None
    try:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        vectorizer = VertexAITextVectorizer(
            model=settings.EMBEDDING_MODEL,
            api_config={
                "project_id": settings.PROJECT_ID,
                "location": settings.LOCATION,
            },
        )
        _cache = SemanticCache(
            name="rag_cache",
            redis_url=redis_url,
            prefix="semantic",
            distance_threshold=DISTANCE_THRESHOLD,
            ttl=CACHE_TTL,
            vectorizer=vectorizer,
        )
        try:
            _cache.index.create(overwrite=False)
            logfire.info(f"✅ Redis Semantic Cache Initialized at {settings.REDIS_HOST}")
        except Exception as e:
            logfire.warning(f"⚠️ Redis Index Error: {e}. Semantic Search might not be supported on this Redis instance. Caching disabled.")
            _cache = None
        return _cache
    except Exception as e:
        logfire.error(f"❌ Redis Cache Connection Failed: {e}")
        _cache = None
        return None

def check_cache(query: str):
    """
    check if the question is in cache if it is then return the answer from cache
    """
    if not _cache:
        return None
    try:
        results = _cache.check(prompt=query)
        if results:
            logfire.info(f"✅ Cache Hit for query: {query}")
            return results[0]["response"]
        return None
    except Exception as e:
        logfire.error(f"❌ Cache Query Error: {e}")
        return None
def update_cache(query:str, response:str):
    """
    Update the cache with a new query and its response.
    """
    if not _cache:
        return
    try:
        _cache.store(prompt=query, response=response, ttl=CACHE_TTL)
        logfire.info("💾 Cache Updated with new response")
    except Exception as e:
        logfire.error(f"❌ Cache Update Error: {e}")
# Initialize on module load
init_cache()