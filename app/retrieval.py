from sqlalchemy import select
from sqlalchemy.orm import Session

from .embeddings import embed_texts
from .models import Movie


def search_movies(db: Session, query: str, top_k: int = 5, filters: dict | None = None):
    filters = filters or {}
    query_embedding = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]

    distance = Movie.embedding.cosine_distance(query_embedding).label("distance")
    stmt = select(Movie, distance)

    genre = filters.get("genre")
    if genre:
        stmt = stmt.where(Movie.genres.ilike(f"%{genre}%"))

    min_year = filters.get("min_year")
    if min_year is not None:
        stmt = stmt.where(Movie.year >= min_year)

    max_year = filters.get("max_year")
    if max_year is not None:
        stmt = stmt.where(Movie.year <= max_year)

    stmt = stmt.order_by(distance).limit(top_k)

    return [
        {"movie": movie, "score": 1 - distance}
        for movie, distance in db.execute(stmt)
    ]
