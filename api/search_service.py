from typing import Optional, List
from datetime import datetime

class SearchService:
    def __init__(self):
        self._history: List[dict] = []

    async def search(self, query: str, notebook_id: Optional[str] = None, limit: int = 10, filters: Optional[dict] = None) -> List[dict]:
        if not query or not query.strip():
            return []
        return await self._execute_search(query, notebook_id, limit, filters)

    async def get_search_history(self, notebook_id: Optional[str] = None, limit: int = 20) -> List[dict]:
        entries = self._history
        if notebook_id:
            entries = [e for e in entries if e.get("notebook_id") == notebook_id]
        return sorted(entries, key=lambda e: e.get("timestamp", ""), reverse=True)[:limit]

    async def log_search(self, query: str, notebook_id: Optional[str] = None, result_count: int = 0):
        self._history.append({"query": query, "notebook_id": notebook_id, "result_count": result_count, "timestamp": datetime.now().isoformat()})

    async def _execute_search(self, query: str, notebook_id: Optional[str], limit: int, filters: Optional[dict]) -> List[dict]:
        return []
