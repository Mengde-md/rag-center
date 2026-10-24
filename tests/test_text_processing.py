import pytest

from app.providers.parsers.plain_text import PlainTextParser
from app.utils.text_splitter import CharacterTextSplitter


def test_unicode_chunks_preserve_offsets_and_overlap():
    text = "退款政策：用户可在七天内申请退款。"
    chunks = CharacterTextSplitter(8, 2).split(text)
    assert chunks[0].start_char == 0
    assert chunks[-1].end_char == len(text)
    assert all(chunk.content == text[chunk.start_char : chunk.end_char] for chunk in chunks)
    assert all(chunk.end_char - chunk.start_char <= 8 for chunk in chunks)
    assert all(
        left.end_char - right.start_char == 2
        for left, right in zip(chunks, chunks[1:], strict=False)
    )
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_splitter_handles_exact_boundaries_and_blank_input():
    splitter = CharacterTextSplitter(4, 1)
    assert [chunk.content for chunk in splitter.split("1234")] == ["1234"]
    assert [chunk.content for chunk in splitter.split("1234567")] == ["1234", "4567"]
    assert splitter.split("   \n") == []


@pytest.mark.parametrize("size,overlap", [(0, 0), (8, 8), (8, -1)])
def test_splitter_rejects_non_progressing_windows(size, overlap):
    with pytest.raises(ValueError):
        CharacterTextSplitter(size, overlap)


def test_plain_text_parser_normalizes_markdown_without_interpreting_it():
    parsed = PlainTextParser().parse("\ufeff# 政策\r\n正文\r下一行")
    assert parsed.text == "# 政策\n正文\n下一行"
    with pytest.raises(ValueError):
        PlainTextParser().parse("\ufeff \r\n")
