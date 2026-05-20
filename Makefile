PROJECT_NAME := zero-trust
FRONTEND_IMAGE := zero-trust-frontend
BACKEND_IMAGE := zero-trust-backend
COMPOSE_FRONTEND_IMAGE := cloud-computing-main-frontend
COMPOSE_BACKEND_IMAGE := cloud-computing-main-backend
K8S_DIR := k8s
AWS_SECRET := zero-trust-aws-secrets

.PHONY: help install frontend backend build build-frontend build-backend up down logs ps restart \
	k8s-secret k8s-apply k8s-delete k8s-status k8s-logs clean-docker clean-k8s clean-images fresh

help:
	@echo Zero Trust Cloud-Native Project
	@echo.
	@echo Local development:
	@echo   make install        Install frontend and backend dependencies
	@echo   make frontend       Run React/Vite frontend locally
	@echo   make backend        Run FastAPI backend locally
	@echo.
	@echo Docker:
	@echo   make build          Build frontend and backend Docker images
	@echo   make up             Start full Docker Compose stack
	@echo   make down           Stop Docker Compose stack
	@echo   make logs           Follow Docker Compose logs
	@echo   make ps             Show Docker Compose containers
	@echo   make restart        Rebuild and restart Docker Compose stack
	@echo.
	@echo Kubernetes:
	@echo   make k8s-secret     Show the command to create the AWS secret
	@echo   make k8s-apply      Apply Kubernetes manifests
	@echo   make k8s-delete     Delete Kubernetes manifests and AWS secret
	@echo   make k8s-status     Show pods, services, and ingress
	@echo   make k8s-logs       Show backend logs
	@echo.
	@echo Cleanup:
	@echo   make clean-docker   Stop Compose and remove project containers/volumes
	@echo   make clean-k8s      Delete project Kubernetes resources and secret
	@echo   make clean-images   Remove project Docker images
	@echo   make fresh          Clean Kubernetes, Docker stack, and project images

install:
	npm install
	cd backend && .\.venv\Scripts\python.exe -m pip install -r requirements.txt

frontend:
	npm run dev

backend:
	cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

build: build-frontend build-backend

build-frontend:
	docker build -t $(FRONTEND_IMAGE) .

build-backend:
	docker build -t $(BACKEND_IMAGE) ./backend

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

restart:
	docker compose down
	docker compose up --build

k8s-secret:
	@echo Run this with your real AWS credentials:
	@echo kubectl create secret generic $(AWS_SECRET) --from-literal=AWS_REGION=eu-north-1 --from-literal=S3_BUCKET_NAME=zerotrustx-secure-storage --from-literal=AWS_ACCESS_KEY_ID=your-real-access-key --from-literal=AWS_SECRET_ACCESS_KEY=your-real-secret-key --from-literal=AWS_SESSION_TOKEN=

k8s-apply:
	kubectl apply -f $(K8S_DIR)/

k8s-delete:
	-kubectl delete -f $(K8S_DIR)/ --ignore-not-found=true
	-kubectl delete secret $(AWS_SECRET) --ignore-not-found=true

k8s-status:
	kubectl get pods
	kubectl get services
	kubectl get ingress

k8s-logs:
	kubectl logs deployment/zero-trust-backend

clean-docker:
	-docker compose down --remove-orphans --volumes
	-docker rm -f zero-trust-frontend zero-trust-backend

clean-k8s:
	-kubectl delete -f $(K8S_DIR)/ --ignore-not-found=true
	-kubectl delete secret $(AWS_SECRET) --ignore-not-found=true

clean-images:
	-docker rmi -f $(FRONTEND_IMAGE) $(BACKEND_IMAGE) $(COMPOSE_FRONTEND_IMAGE) $(COMPOSE_BACKEND_IMAGE)

fresh: clean-k8s clean-docker clean-images
	@echo Project Docker and Kubernetes resources have been cleaned.
