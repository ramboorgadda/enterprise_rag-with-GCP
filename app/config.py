import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()


def _normalize_qdrant_url(raw_url: str) -> str:
    url = (raw_url or "").strip().rstrip("/")
    if not url:
        return ""

    parsed = urlparse(url)
    # Qdrant Cloud REST commonly expects explicit :6333.
    if parsed.scheme in {"http", "https"} and parsed.hostname and parsed.port is None and "cloud.qdrant.io" in parsed.hostname:
        netloc = f"{parsed.hostname}:6333"
        if parsed.username and parsed.password:
            netloc = f"{parsed.username}:{parsed.password}@{netloc}"
        elif parsed.username:
            netloc = f"{parsed.username}@{netloc}"
        parsed = parsed._replace(netloc=netloc)

    return urlunparse(parsed).rstrip("/")


class Settings:
    PROJECT_ID = os.getenv("PROJECT_ID", "enterprise-rag-497423")
    LOCATION = os.getenv("LOCATION", "us-central1")
    GCP_DOC_AI_LOCATION = os.getenv("GCP_DOC_AI_LOCATION", "us")
    GCP_DOC_AI_PROCESSOR_ID = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    RAW_BUCKET = os.getenv("GCP_RAW_BUCKET", "enterprise-rag-raw-1234")
    PROCESSED_BUCKET = os.getenv("GCP_PROCESSED_BUCKET", "enterprise-rag-processed-1234")

    QDRANT_URL = _normalize_qdrant_url(
        os.getenv("QDRANT_CLUSTER_ENDPOINT")
        or os.getenv("QDRANT_URL")
        or ""
    )
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = "enterprise_rag"

    # --- REASONING ENGINE (GROQ) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama-3.3-70b-versatile"

    # --- EMBEDDINGS (VERTEX AI) ---
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

    # --- DATABASE & CACHE ---
    DB_USER = os.getenv("DB_USER", "rag_admin")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME", "rag_memory")
    DB_CONNECTION_NAME = os.getenv("DB_CONNECTION_NAME")
    
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")

    # --- ENVIRONMENT MODE ---
    # Set to "true" in your local .env to bypass Cloud SQL/Redis
    LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() == "true"

    # --- OBSERVABILITY ---
    LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "entreprise_rag")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Apply LangChain environment variables for automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

settings = Settings()