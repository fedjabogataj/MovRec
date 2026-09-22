from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .db import get_db
from .models import Movie
from .schemas import MovieOut

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
