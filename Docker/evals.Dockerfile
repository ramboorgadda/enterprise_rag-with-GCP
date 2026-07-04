# --- EVALS MICROSERVICE (STREAMLIT) ---
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run settings
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

EXPOSE 8501

# Start the Evals Streamlit application
CMD ["streamlit", "run", "evals/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
