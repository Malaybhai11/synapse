from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])

class BookmarkCreate(BaseModel):
    item_id: str
    item_type: str
    label: Optional[str] = None

class Bookmark(BaseModel):
    id: str
    item_id: str
    item_type: str
    label: Optional[str] = None
    created_at: str

_in_memory_bookmarks: List[Bookmark] = []

@router.post("/")
async def add_bookmark(bookmark: BookmarkCreate):
    new_bookmark = Bookmark(id=f"bm-{len(_in_memory_bookmarks) + 1}",
        item_id=bookmark.item_id, item_type=bookmark.item_type,
        label=bookmark.label, created_at=datetime.now().isoformat())
    _in_memory_bookmarks.append(new_bookmark)
    return new_bookmark

@router.get("/")
async def list_bookmarks(item_type: Optional[str] = None):
    if item_type:
        return [b for b in _in_memory_bookmarks if b.item_type == item_type]
    return _in_memory_bookmarks

@router.delete("/{bookmark_id}")
async def remove_bookmark(bookmark_id: str):
    for i, b in enumerate(_in_memory_bookmarks):
        if b.id == bookmark_id:
            _in_memory_bookmarks.pop(i)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Bookmark not found")
