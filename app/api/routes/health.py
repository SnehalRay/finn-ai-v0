from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "agent": "Finn v0"}
