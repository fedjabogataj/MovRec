import logging
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from google.genai import errors as genai_errors
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .db import get_db
from .llm import chat
from .models import Movie
from .retrieval import search_movies
from .schemas import ChatRequest, ChatResponse, MovieOut, MovieSearchResult, SearchRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("movrec")

app = FastAPI()

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("request received: %s %s", request.method, request.url.path)
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "response sent: %s %s -> %d (%.0fms)",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except OperationalError:
        logger.exception("health check failed: database unreachable")
        raise HTTPException(status_code=503, detail="Database unreachable")
    return {"status": "ok"}


@app.get("/movies", response_model=list[MovieOut])
def list_movies(
    genre: str | None = None,
    min_year: int | None = None,
    max_year: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Movie)
    if genre:
        query = query.where(Movie.genres.ilike(f"%{genre}%"))
    if min_year is not None:
        query = query.where(Movie.year >= min_year)
    if max_year is not None:
        query = query.where(Movie.year <= max_year)
    return db.execute(query).scalars().all()


@app.get("/movies/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if movie is None: raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.post("/search", response_model=list[MovieSearchResult])
def search(request: SearchRequest, db: Session = Depends(get_db)):
    filters = {
        "genre": request.genre,
        "min_year": request.min_year,
        "max_year": request.max_year,
    }
    results = search_movies(db, request.query, top_k=request.top_k, filters=filters)
    return [
        MovieSearchResult(
            id=r["movie"].id,
            title=r["movie"].title,
            year=r["movie"].year,
            genres=r["movie"].genres,
            description=r["movie"].description,
            score=r["score"],
        )
        for r in results
    ]


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        conversation_id, reply = chat(db, request.conversation_id, request.message)
    except genai_errors.APIError:
        logger.exception("chat failed: Gemini API error")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    return ChatResponse(conversation_id=conversation_id, reply=reply)
