import io
from distro import name
import logfire
from pypdf import PdfReader, PdfWriter
from google.cloud import documentai
from app.config import settings
client = documentai.DocumentProcessorServiceClient()
MAX_PAGES_PER_REQUEST =15
def parse_pdf(file_path: str):
    """
    Parses PDF files using Google Cloud Document AI.
    Handles multi-page PDFs by batching pages into requests.
    Extracts text content for RAG.
    """
    with logfire.span("📄 PDF Parsing", filename=file_path):
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            logfire.info(f"Total pages in PDF: {total_pages}")
            name = client.processor_path(
                settings.PROJECT_ID, 
                settings.GCP_DOC_AI_LOCATION, 
                settings.GCP_DOC_AI_PROCESSOR_ID
            )
            full_text = ""
            if total_pages <= MAX_PAGES_PER_REQUEST:
                with open(file_path, "rb") as f:
                    image_content = f.read()
                full_text = process_document_chunk(image_content, name)
            else:
                # Split into chunks of MAX_PAGES_PER_REQUEST
                logfire.info(f"PDF exceeds {MAX_PAGES_PER_REQUEST} pages. Splitting into chunks...")
                for i in range(0, total_pages, MAX_PAGES_PER_REQUEST):
                        writer = PdfWriter()
                        chunk_end = min(i + MAX_PAGES_PER_REQUEST, total_pages)
                        
                        for page_num in range(i, chunk_end):
                            writer.add_page(reader.pages[page_num])
                        
                        # Write chunk to bytes
                        with io.BytesIO() as bytes_stream:
                            writer.write(bytes_stream)
                            chunk_bytes = bytes_stream.getvalue()
                            
                        with logfire.span(f"Processing pages {i+1} to {chunk_end}"):
                            chunk_text = process_document_chunk(chunk_bytes, name)
                            full_text += chunk_text + "\n"
        except Exception as e:
            logfire.error(f"Error parsing PDF file {file_path}: {e}")
            raise e
def process_document_chunk(image_content: bytes, name: str) -> str:
    """Helper function to send a specific byte chunk to Document AI"""
    raw_document = documentai.RawDocument(
        content=image_content, 
        mime_type="application/pdf"
    )

    request = documentai.ProcessRequest(
        name=name, 
        raw_document=raw_document
    )

    result = client.process_document(request=request)
    return result.document.text