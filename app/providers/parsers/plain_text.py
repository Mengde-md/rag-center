from app.providers.parsers.base import DocumentParser, ParsedDocument


class PlainTextParser(DocumentParser):
    def parse(self, content: str) -> ParsedDocument:
        # Markdown is passed through as text. Normalize line endings for stable offsets.
        text = content.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
        if not text.strip():
            raise ValueError("document contains no indexable text")
        return ParsedDocument(text=text, metadata={"source_type": "text"})
