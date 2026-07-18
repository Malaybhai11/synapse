from typing import List
import json
from datetime import datetime

class ExportService:
    def export_to_markdown(self, notes: List[dict]) -> str:
        lines = ["# Exported Notes", f"*Exported: {datetime.now().isoformat()}*"]
        for note in sorted(notes, key=lambda n: n.get("created_at", "")):
            title = note.get("title", "Untitled")
            content = note.get("content", "")
            tags = note.get("tags", [])
            lines.append(f"## {title}")
            if tags:
                lines.append(f"*Tags: {', '.join(tags)}*")
            lines.append(content)
            lines.append("---")
        return "\n".join(lines)

    def export_to_json(self, notes: List[dict]) -> str:
        export_data = {"exported_at": datetime.now().isoformat(), "count": len(notes),
            "notes": [{"title": n.get("title"), "content": n.get("content"),
                "tags": n.get("tags", []), "created_at": str(n.get("created_at", "")),
                "updated_at": str(n.get("updated_at", ""))} for n in notes]}
        return json.dumps(export_data, indent=2)

    def export_to_csv(self, notes: List[dict]) -> str:
        lines = ["title,content,tags,created_at"]
        for note in notes:
            t = note.get("title", "").replace('"', '""')
            c = note.get("content", "").replace('"', '""').replace("\n", "\\n")[:200]
            tags = " ".join(note.get("tags", []))
            cr = str(note.get("created_at", ""))
            lines.append(f'"{t}","{c}","{tags}","{cr}"')
        return "\n".join(lines)
