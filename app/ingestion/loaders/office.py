import logfire 
from unstructured.partition.auto import partition

def parse_office(file_path:str):
    """
    Parses Office documents (Word, Excel, PowerPoint) using unstructured.
    Extracts text content for RAG.
    """
    with logfire.span("📄 Office Parsing", filename=file_path):
        try:
            elements = partition(file_path)
            full_text = "\n".join([str(e1) for e1 in elements])
            if not full_text.strip():
                logfire.warning(f"No text extracted from {file_path}. Check if the file is valid and supported.")
            else:
                logfire.info(f"Successfully extracted text from {file_path}.")
            return full_text
        except Exception as e:
            logfire.error(f"Error parsing Office file {file_path}: {e}")
            raise e