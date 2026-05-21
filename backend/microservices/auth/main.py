import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.verify import router as verify_router
from app.routes.access import router as access_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

app = FastAPI(title="Auth & Zero Trust Microservice", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verify_router)
app.include_router(verify_router, prefix="/api")
app.include_router(access_router)
app.include_router(access_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth"}
