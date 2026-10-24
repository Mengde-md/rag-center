from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

T = TypeVar("T")
ExternalId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*")
    @classmethod
    def reject_nul_characters(cls, value):
        if isinstance(value, str) and "\x00" in value:
            raise ValueError("text fields must not contain NUL characters")
        return value


class ResponseEnvelope(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: T | None = None
