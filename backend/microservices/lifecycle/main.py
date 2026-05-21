import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.delete import router as delete_router
from app.routes.expiry import router as expiry_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

app = FastAPI(title="Lifecycle Microservice", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(delete_router)
app.include_router(delete_router, prefix="/api")
app.include_router(expiry_router)
app.include_router(expiry_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lifecycle"}
