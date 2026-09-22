from pydantic import BaseModel, ConfigDict, Field


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: int | None
    genres: str
    description: str


class MovieSearchResult(MovieOut):
    score: float


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    genre: str | None = None
    min_year: int | None = None
    max_year: int | None = None


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
