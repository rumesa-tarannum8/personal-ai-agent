from pydantic import BaseModel, Field, field_validator


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped


class MemoryUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped


class MemoryOut(BaseModel):
    id: int
    content: str
    approved: bool
    created_at: str
    updated_at: str


class MemoryListOut(BaseModel):
    items: list[MemoryOut]


class MemoryHit(MemoryOut):
    score: float


class MemoryRetrieveOut(BaseModel):
    items: list[MemoryHit]


class ErrorOut(BaseModel):
    detail: str
