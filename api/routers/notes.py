from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/notes", tags=["notes"])

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    per_page: int
    total_pages: int

@router.get("/")
async def list_notes_paginated(notebook_id: Optional[str] = None, page: int = 1, per_page: int = 20):
    from api.notes_service import NotesService
    service = NotesService()
    notes, total = await service.list_paginated(
        notebook_id=notebook_id,
        offset=(page - 1) * per_page,
        limit=per_page,
    )
    return PaginatedResponse(items=notes, total=total, page=page, per_page=per_page, total_pages=-(-total // per_page))
