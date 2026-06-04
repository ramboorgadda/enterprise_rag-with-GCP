import logfire
import os
import sys
import uuid
import json
import vertexai

from typing import List
from google.cloud import storage
from qdrant_client import QdrantClient
from qdrant_client.http import models


# Import Local Modules
from app.config import settings
from app.services.retrieval.embedding import embed_texts
from app.ingestion.loaders.text import parse_text
from app.ingestion.loaders.pdf import parse_pdf
from app.ingestion.loaders.office import parse_office
from app.ingestion.chunking.splitters import chunk_text
