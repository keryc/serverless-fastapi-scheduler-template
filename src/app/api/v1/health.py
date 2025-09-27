from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["meta"])
def health() -> dict[str, bool]:
    return {"ok": True}
