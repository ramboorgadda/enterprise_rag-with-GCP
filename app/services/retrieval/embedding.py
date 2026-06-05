import vertexai
from vertexai.language_models import TextEmbeddingModel
from app.config import settings
model = None
BATCH_SIZE =50
def get_embedding_model():
    global model
    if model is None:
        vertexai.init(project=settings.PROJECT_ID, location=settings.LOCATION)
        model = TextEmbeddingModel.from_pretrained(settings.EMBEDDING_MODEL)
    return model

def embed_query(query: str):
    """
    Generates an embedding vector for a given query using Vertex AI's TextEmbeddingModel.
    """
    embedding_model = get_embedding_model()
    embedding = embedding_model.get_embeddings([query])[0]
    return embedding.values

def embed_texts(texts: list[str]):
    """
    Generates embedding vectors for a list of texts in batches.
    Handles large lists by processing them in chunks to avoid memory issues.
    """
    embedding_model = get_embedding_model()
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        batch_embeddings = embedding_model.get_embeddings(batch)
        all_embeddings.extend([embedding.values for embedding in batch_embeddings])
    return all_embeddings