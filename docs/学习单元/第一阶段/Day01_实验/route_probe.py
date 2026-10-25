"""Inspect the real app's OpenAPI contract without starting lifespan or a server."""

import argparse
from copy import deepcopy
from typing import Any

EXPECTED_OPERATIONS = frozenset(
    {
        ("post", "/api/v1/knowledge-bases/create"),
        ("post", "/api/v1/documents/upload"),
        ("post", "/api/v1/rag/retrieve"),
    }
)
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "options", "head", "trace"})


def collect_operations(schema: dict[str, Any]) -> set[tuple[str, str]]:
    """Return HTTP operations; path-level metadata such as parameters is not a route."""
    return {
        (method, path)
        for path, path_item in schema.get("paths", {}).items()
        for method in path_item
        if method in HTTP_METHODS
    }


def assert_core_contract(schema: dict[str, Any]) -> list[tuple[str, str]]:
    """Report missing and unexpected operations, including method mismatches."""
    actual = collect_operations(schema)
    missing = EXPECTED_OPERATIONS - actual
    unexpected = actual - EXPECTED_OPERATIONS
    if missing or unexpected:
        details = []
        for label, values in (("missing", missing), ("unexpected", unexpected)):
            if values:
                operations = ", ".join(
                    f"{method.upper()} {path}" for method, path in sorted(values)
                )
                details.append(f"{label}: {operations}")
        raise ValueError("; ".join(details))
    return sorted(actual)


def main() -> None:
    from app.main import create_app

    parser = argparse.ArgumentParser(description="Inspect the RAG business contract")
    parser.add_argument("--simulate", choices=("missing", "method", "extra"))
    args = parser.parse_args()
    application = create_app()
    schema = deepcopy(application.openapi())
    path = "/api/v1/rag/retrieve"
    if args.simulate == "missing":
        del schema["paths"][path]
    elif args.simulate == "method":
        item = schema["paths"][path]
        item["get"] = item.pop("post")
    elif args.simulate == "extra":
        schema["paths"]["/api/v1/answer"] = {"post": {}}
    operations = assert_core_contract(schema)
    print(f"Business operations: {len(operations)}")
    for method, path in operations:
        print(f"{method.upper()} {path}")
    print("Scope: schema only; database, model requests and lifespan were not run.")


if __name__ == "__main__":
    main()
