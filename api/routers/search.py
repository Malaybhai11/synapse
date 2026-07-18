from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str
    notebook_id: Optional[str] = None
    limit: int = 10
    filters: Optional[dict] = None

@router.get("/history")
async def get_search_history(notebook_id: Optional[str] = None, limit: int = 20):
    from api.search_service import SearchService
    service = SearchService()
    return await service.get_search_history(notebook_id=notebook_id, limit=limit)

@router.post("/")
async def search(request: SearchRequest):
    from api.search_service import SearchService
    service = SearchService()
    results = await service.search(request.query, request.notebook_id, request.limit, request.filters)
    await service.log_search(request.query, request.notebook_id, len(results))
    return {"results": results, "total": len(results)}
