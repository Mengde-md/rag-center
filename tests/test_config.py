import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    "values",
    [
        {"chunk_size": 100, "chunk_overlap": 100},
        {"database_url": "sqlite:///test.db"},
        {"embedding_dimensions": 2001},
        {"top_k": 0},
        {"vector_store": "unsupported"},
        {"model_base_url": "file:///tmp/model"},
    ],
)
def test_invalid_configuration_fails_early(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://user:example@example.test/v1",
        "https://user@example.test/v1",
        "https://bad host.test/v1",
        "https://example.test/v1\n",
        "https://example.test:invalid/v1",
        "https://example.test:70000/v1",
        "https://:443/v1",
        "https://example.test/v1?",
        "https://example.test/v1#",
    ],
)
def test_invalid_model_endpoints_are_rejected_before_requests(base_url):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, model_base_url=base_url)
    assert "MODEL_BASE_URL" in str(error.value)
    assert base_url not in str(error.value)
    assert "input_value" not in str(error.value)


@pytest.mark.parametrize(
    "base_url,expected",
    [
        ("https://example.test/v1/", "https://example.test/v1"),
        ("http://localhost:8080/v1", "http://localhost:8080/v1"),
        ("http://[::1]:8080/v1/", "http://[::1]:8080/v1"),
    ],
)
def test_model_endpoints_preserve_supported_hosts_and_path_prefixes(base_url, expected):
    assert Settings(_env_file=None, model_base_url=base_url).model_base_url == expected
