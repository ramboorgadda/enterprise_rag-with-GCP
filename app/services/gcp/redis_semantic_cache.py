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
import json
import hashlib
import numpy as np
import logfire

DISTANCE_THRESHOLD = float(os.getenv("CACHE_DISTANCE_THRESHOLD", "0.15"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
KEY_PREFIX = "sem_cache:"

_client = None

def _get_client():
    """
    Returns a Redis client connected to the configured host and port.
    """
    global _client
    if _client is not None:
        return _client
    try:
        import redis
        redis_host = os.getenv("REDIS_HOST")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        if not redis_host:
            logfire.warning("REDIS_HOST is not set. Semantic cache will be disabled.")
            return None
        _client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        logfire.info(f"✅ Connected to Redis at {redis_host}:{redis_port}")
        return _client
    except Exception as e:
        logfire.error(f"Failed to connect to Redis: {e}")
        return None