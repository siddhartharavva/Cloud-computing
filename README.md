# Cloud-Native Zero Trust Secure Data Exchange

Cloud-native Zero Trust file verification and secure upload platform.

Current architecture:

```text
React/Vite frontend -> FastAPI backend -> Amazon S3
```

The frontend provides the upload and verification UI. The FastAPI backend handles API requests, uploads files to Amazon S3, and returns file metadata such as file ID and S3 object key.

## Project Structure

```text
Cloud-computing-main/
├── src/                     React frontend
├── backend/
│   ├── app/
│   │   ├── main.py          FastAPI app setup
│   │   ├── config.py        Backend environment configuration
│   │   ├── routes/          API routes
│   │   ├── services/        S3 integration
│   │   └── models/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── k8s/                     Kubernetes manifests
├── Dockerfile               Frontend production image
├── nginx.conf               Frontend nginx + API proxy config
├── docker-compose.yml
├── package.json
└── .env.example
```

## Environment

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Set real AWS values before S3 uploads:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_MODE=true

AWS_REGION=eu-north-1
S3_BUCKET_NAME=zerotrustx-secure-storage
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SESSION_TOKEN=
```

Do not commit `.env`.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
npm install
npm run dev
```

Local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## API Endpoints

Implemented:

- `GET /`
- `GET /health`
- `POST /upload`
- `POST /verify`

Container/ingress-compatible aliases:

- `POST /api/upload`
- `POST /api/verify`

Upload response:

```json
{
  "message": "File uploaded successfully.",
  "filename": "example.pdf",
  "file_id": "generated-uuid",
  "s3_key": "uploads/generated-uuid-example.pdf"
}
```

## Docker

Build images:

```bash
docker build -t zero-trust-frontend .
docker build -t zero-trust-backend ./backend
```

Run the full stack:

```bash
docker compose up --build
```

Stop the stack:

```bash
docker compose down
```

Docker URLs:

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- Frontend API proxy: `http://localhost:8080/api`

## Makefile Shortcuts

If `make` is installed, the project-level `Makefile` provides common commands:

```bash
make build
make up
make down
make k8s-apply
make k8s-status
make fresh
```

`make fresh` removes this project's Kubernetes resources, Docker Compose stack, containers, volumes, and project Docker images.

## Kubernetes

Build local images for a basic local cluster:

```bash
docker build -t zero-trust-frontend .
docker build -t zero-trust-backend ./backend
```

Create the AWS secret in your cluster:

```bash
kubectl create secret generic zero-trust-aws-secrets \
  --from-literal=AWS_REGION=eu-north-1 \
  --from-literal=S3_BUCKET_NAME=zerotrustx-secure-storage \
  --from-literal=AWS_ACCESS_KEY_ID=your-access-key-id \
  --from-literal=AWS_SECRET_ACCESS_KEY=your-secret-access-key \
  --from-literal=AWS_SESSION_TOKEN=
```

Apply manifests:

```bash
kubectl apply -f k8s/
```

Inspect resources:

```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

Manifests included:

- `k8s/frontend-deployment.yaml`
- `k8s/frontend-service.yaml`
- `k8s/backend-deployment.yaml`
- `k8s/backend-service.yaml`
- `k8s/ingress.yaml`

Ingress routing:

- `/` -> frontend
- `/api` -> backend

## Current Scope

Included:

- React/Vite frontend
- FastAPI backend
- Direct multipart upload through backend
- Amazon S3 storage
- Dockerized frontend and backend
- Docker Compose orchestration
- Lightweight Kubernetes manifests

Not included yet:

- DynamoDB
- Authentication enforcement
- Helm
- Istio
- EKS-specific setup
