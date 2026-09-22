from pydantic import BaseModel, ConfigDict


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
    query: str
    top_k: int = 5
    genre: str | None = None
    min_year: int | None = None
    max_year: int | None = None


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
