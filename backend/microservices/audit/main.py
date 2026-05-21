import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.dashboard import router as dashboard_router
from app.routes.logs import router as logs_router
from app.routes.alerts import router as alerts_router
from app.routes.services_status import router as services_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

app = FastAPI(title="Audit Microservice", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(dashboard_router, prefix="/api")
app.include_router(logs_router)
app.include_router(logs_router, prefix="/api")
app.include_router(alerts_router)
app.include_router(alerts_router, prefix="/api")
app.include_router(services_router)
app.include_router(services_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "audit"}
