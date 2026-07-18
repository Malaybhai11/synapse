from typing import List, Optional

class EmbeddingService:
    def __init__(self):
        self._dimension = 768
        self._cache: dict = {}

    async def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dimension
        if text in self._cache:
            return self._cache[text]
        embedding = await self._embed(text)
        self._cache[text] = embedding
        return embedding

    async def batch_embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        valid_texts = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        if not valid_texts:
            return [[0.0] * self._dimension] * len(texts)
        indices, clean_texts = zip(*valid_texts)
        embeddings = [await self.generate_embedding(t) for t in clean_texts]
        result = [[0.0] * self._dimension] * len(texts)
        for idx, emb in zip(indices, embeddings):
            result[idx] = emb
        return result

    async def _embed(self, text: str) -> List[float]:
        import hashlib
        import numpy as np
        seed = hashlib.sha256(text.encode()).hexdigest()
        rng = np.random.RandomState(int(seed[:8], 16))
        return rng.randn(self._dimension).tolist()
