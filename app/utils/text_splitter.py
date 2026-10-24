from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    content: str
    index: int
    start_char: int
    end_char: int


class TextSplitter(ABC):
    @abstractmethod
    def split(self, text: str) -> list[TextChunk]:
        """Split text and retain offsets for future citations."""


class CharacterTextSplitter(TextSplitter):
    """Deterministic Unicode character windows; size/overlap are not token counts."""

    def __init__(self, chunk_size: int, chunk_overlap: int):
        if chunk_size <= 0 or not 0 <= chunk_overlap < chunk_size:
            raise ValueError("require chunk_size > chunk_overlap >= 0")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[TextChunk]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            content = text[start:end]
            if content.strip():
                chunks.append(TextChunk(content, len(chunks), start, end))
            if end == len(text):
                break
            start = end - self.chunk_overlap
        return chunks
