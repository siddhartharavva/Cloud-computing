FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (assuming Docker context is backend root)
COPY . .

# Ensure app module is reachable
ENV PYTHONPATH=/app

# Start the Audit Microservice
CMD ["uvicorn", "microservices.audit.main:app", "--host", "0.0.0.0", "--port", "80"]
