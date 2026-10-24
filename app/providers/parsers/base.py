from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> ParsedDocument:
        """Parse a source into text; future implementations may extract PDF/office content."""
