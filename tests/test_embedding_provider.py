import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import EmbeddingError
from app.providers.embedding.openai_compatible import OpenAICompatibleEmbeddingProvider


def config(**kwargs):
    return Settings(
        _env_file=None,
        model_api_key="test-key",
        embedding_dimensions=3,
        embedding_batch_size=2,
        **kwargs,
    )


async def test_batches_inputs_and_restores_response_order():
    batches = []

    def handler(request):
        import json

        payload = json.loads(request.content)
        batches.append(payload["input"])
        assert str(request.url) == "https://example.test/v1/embeddings"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert payload["encoding_format"] == "float"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": i, "embedding": [float(start), 1.0, 0.0]}
                    for i, start in reversed(list(enumerate(payload["input"])))
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleEmbeddingProvider(
            client, config(model_base_url="https://example.test/v1/")
        )
        assert await provider.embed_texts(["1", "2", "3"]) == [
            [1.0, 1.0, 0.0],
            [2.0, 1.0, 0.0],
            [3.0, 1.0, 0.0],
        ]
        assert await provider.embed_texts([]) == []
    assert batches == [["1", "2"], ["3"]]


@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"index": 1, "embedding": [1.0, 0.0, 0.0]}],
        [{"index": 0, "embedding": [1.0, 0.0]}],
        [{"index": 0, "embedding": [0.0, 0.0, 0.0]}],
        [{"index": 0, "embedding": ["bad", 0.0, 1.0]}],
        [{"index": 0, "embedding": [1.0, 0.0, 0.0]}, {"index": 0, "embedding": [1.0, 0.0, 0.0]}],
    ],
)
async def test_rejects_malformed_or_unusable_embeddings(data):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": data}))
    ) as client:
        with pytest.raises(EmbeddingError):
            await OpenAICompatibleEmbeddingProvider(client, config()).embed_texts(["退款"])


async def test_rejects_non_finite_vectors():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b'{"data":[{"index":0,"embedding":[NaN,1,0]}]}')
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(EmbeddingError, match="non-finite"):
            await OpenAICompatibleEmbeddingProvider(client, config()).embed_query("query")


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_upstream_errors_do_not_expose_response_body(status):
    transport = httpx.MockTransport(lambda request: httpx.Response(status, text="secret-token"))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(EmbeddingError) as error:
            await OpenAICompatibleEmbeddingProvider(client, config()).embed_query("query")
    assert str(status) in error.value.msg
    assert "secret-token" not in error.value.msg


async def test_timeout_is_reported_as_provider_failure():
    def timeout(request):
        raise httpx.ReadTimeout("private upstream URL", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(EmbeddingError, match="timed out"):
            await OpenAICompatibleEmbeddingProvider(client, config()).embed_query("query")
