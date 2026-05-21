import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.access import router as access_router
from app.routes.alerts import router as alerts_router
from app.routes.dashboard import router as dashboard_router
from app.routes.delete import router as delete_router
from app.routes.expiry import router as expiry_router
from app.routes.logs import router as logs_router
from app.routes.services_status import router as services_router
from app.routes.upload import router as upload_router
from app.routes.verify import router as verify_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="Zero Trust File Verification System",
    description="Backend API for secure file upload, Zero Trust verification, monitoring, and lifecycle enforcement.",
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+):5173$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {"message": "Zero Trust File Verification System API"}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


# Register all routers at / and /api (for ingress/nginx compatibility)
_all_routers = [
    upload_router,
    verify_router,
    dashboard_router,
    logs_router,
    access_router,
    delete_router,
    alerts_router,
    expiry_router,
    services_router,
]

for _router in _all_routers:
    app.include_router(_router)
    app.include_router(_router, prefix="/api")
