import math

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import Settings
from app.core.exceptions import EmbeddingError
from app.providers.embedding.base import EmbeddingProvider


class EmbeddingItem(BaseModel):
    model_config = ConfigDict(strict=True)
    index: int
    embedding: list[float]


class EmbeddingResponse(BaseModel):
    data: list[EmbeddingItem]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self, client: httpx.AsyncClient, settings: Settings):
        self.client = client
        self.settings = settings

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        api_key = self.settings.model_api_key.get_secret_value()
        if not api_key or api_key == "your-api-key":
            raise EmbeddingError("MODEL_API_KEY is not configured")
        vectors: list[list[float]] = []
        size = self.settings.embedding_batch_size
        for start in range(0, len(texts), size):
            batch = texts[start : start + size]
            try:
                response = await self.client.post(
                    f"{self.settings.model_base_url}/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": self.settings.embedding_model,
                        "input": batch,
                        "encoding_format": "float",
                    },
                )
                response.raise_for_status()
                result = EmbeddingResponse.model_validate(response.json())
            except httpx.TimeoutException as exc:
                raise EmbeddingError("embedding provider timed out") from exc
            except httpx.HTTPStatusError as exc:
                raise EmbeddingError(
                    f"embedding provider returned HTTP {exc.response.status_code}"
                ) from exc
            except (httpx.RequestError, ValidationError, ValueError) as exc:
                raise EmbeddingError("embedding provider returned an invalid response") from exc

            ordered = sorted(result.data, key=lambda item: item.index)
            if [item.index for item in ordered] != list(range(len(batch))):
                raise EmbeddingError("embedding provider returned inconsistent input indexes")
            for item in ordered:
                vector = item.embedding
                if len(vector) != self.settings.embedding_dimensions:
                    raise EmbeddingError("embedding dimension does not match EMBEDDING_DIMENSIONS")
                if not all(math.isfinite(value) for value in vector) or not any(vector):
                    raise EmbeddingError("embedding provider returned a non-finite or zero vector")
                vectors.append(vector)
        return vectors
