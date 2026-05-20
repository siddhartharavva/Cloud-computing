# Cloud-Native Zero Trust Secure Data Exchange

Hybrid cloud-native project for a Zero Trust file verification system.

The current architecture is:

```text
React frontend -> FastAPI backend -> Amazon S3
```

The frontend provides the upload and verification UI. The FastAPI backend exposes upload and verification APIs, stores uploaded files in Amazon S3, and is Docker-ready.

## Project Structure

```text
Cloud-computing-main/
├── src/                  React frontend
├── backend/
│   ├── app/
│   │   ├── main.py       FastAPI app setup
│   │   ├── config.py     Backend environment configuration
│   │   ├── routes/       API routes
│   │   ├── services/     S3 integration
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
├── package.json
└── .env.example
```

## Environment Setup

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Update the AWS values before using real S3 upload:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_MODE=true

AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-real-bucket-name
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SESSION_TOKEN=
```

Do not commit `.env`.

## Backend

Install and run FastAPI:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Frontend

Install and run React:

```bash
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

## API Endpoints

Currently implemented:

- `GET /`
- `GET /health`
- `POST /upload`
- `POST /verify`

`POST /upload` accepts multipart form data with a `file` field and stores the file in S3 under:

```text
uploads/
```

Upload response:

```json
{
  "message": "File uploaded successfully.",
  "filename": "example.pdf",
  "file_id": "generated-uuid",
  "s3_key": "uploads/generated-uuid-example.pdf"
}
```

`POST /verify` currently returns a mock verification response:

```json
{
  "status": "verified",
  "integrity": "valid"
}
```

## Docker

Build and run the backend container:

```bash
cd backend
docker build -t zero-trust-backend .
docker run --env-file ../.env -p 8000:8000 zero-trust-backend
```

## Current Scope

Included:

- React frontend
- FastAPI backend
- Direct multipart upload from frontend to backend
- Amazon S3 storage through backend
- Dockerfile for backend
- CORS support for local frontend

Not included yet:

- DynamoDB
- Authentication enforcement
- Kubernetes manifests
- Lambda/API Gateway deployment
