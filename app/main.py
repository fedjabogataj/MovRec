from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .db import get_db
from .llm import chat
from .models import Movie
from .retrieval import search_movies
from .schemas import ChatRequest, ChatResponse, MovieOut, MovieSearchResult, SearchRequest

app = FastAPI()

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
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
    conversation_id, reply = chat(db, request.conversation_id, request.message)
    return ChatResponse(conversation_id=conversation_id, reply=reply)
