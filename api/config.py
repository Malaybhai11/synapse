


import os
from typing import List

class ConfigValidator:
    """Validate required environment configuration on startup."""

    REQUIRED_KEYS: List[str] = ["DATABASE_URL", "SECRET_KEY", "AI_PROVIDER"]

    @classmethod
    def validate(cls) -> List[str]:
        missing = []
        for key in cls.REQUIRED_KEYS:
            if not os.environ.get(key):
                missing.append(key)
        return missing

    @classmethod
    def is_valid(cls) -> bool:
        return len(cls.validate()) == 0

    @classmethod
    def get_missing_message(cls) -> str:
        missing = cls.validate()
        if not missing:
            return "All configuration keys present"
        return f"Missing required config keys: {', '.join(missing)}"
