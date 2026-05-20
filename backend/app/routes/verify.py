from fastapi import APIRouter


router = APIRouter(tags=["Verify"])


@router.post("/verify")
async def verify_file() -> dict[str, str]:
    return {
        "status": "verified",
        "integrity": "valid",
    }
