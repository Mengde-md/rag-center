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
