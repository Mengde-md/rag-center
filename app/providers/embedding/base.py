from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one nonzero, finite embedding per input, in the same order."""

    async def embed_query(self, query: str) -> list[float]:
        return (await self.embed_texts([query]))[0]
