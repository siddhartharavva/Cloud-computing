import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.verify import router as verify_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="Zero Trust File Verification System",
    description="Backend API for local file upload and verification workflows.",
    version="1.0.0",
)


@app.middleware("http")
async def log_cors_preflight(request: Request, call_next):
    if request.method == "OPTIONS":
        logging.info(
            "CORS preflight: origin=%s method=%s headers=%s",
            request.headers.get("origin"),
            request.headers.get("access-control-request-method"),
            request.headers.get("access-control-request-headers"),
        )
        print(f"[CORS DEBUG] origin={request.headers.get('origin')}")
        print(f"[CORS DEBUG] request_method={request.headers.get('access-control-request-method')}")
        print(f"[CORS DEBUG] request_headers={request.headers.get('access-control-request-headers')}")

    return await call_next(request)


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


app.include_router(upload_router)
app.include_router(verify_router)
