from fastapi import APIRouter, Depends

from src.app.core.auth import verify_token
from src.tasks.registry import TaskRegistry

router = APIRouter()


@router.get("/tasks", tags=["tasks"], dependencies=[Depends(verify_token)])
def list_tasks() -> dict[str, list[dict]]:
    """List the registered scheduled tasks. Example of a protected endpoint."""
    return {"tasks": TaskRegistry.list_all()}
