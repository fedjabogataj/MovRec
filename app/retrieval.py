from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .embeddings import embed_texts
from .models import Movie, MovieRating



ALPHA = 0.8          # weight on semantic similarity vs. popularity
RATING_MIN, RATING_MAX = 0.5, 5.0   # MovieLens rating scale


def search_movies(db: Session, query: str, top_k: int = 5, filters: dict | None = None):
    filters = filters or {}
    query_embedding = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]

    similarity = 1 - Movie.embedding.cosine_distance(query_embedding)
    normalized_popularity = func.coalesce(
        (MovieRating.bayesian_avg - RATING_MIN) / (RATING_MAX - RATING_MIN),
        0.5,
    )
    final_score = (ALPHA * similarity + (1 - ALPHA) * normalized_popularity).label("final_score")

    stmt = (
        select(Movie, final_score)
        .outerjoin(MovieRating, Movie.id == MovieRating.id)
    )

    genre = filters.get("genre")
    if genre:
        stmt = stmt.where(Movie.genres.ilike(f"%{genre}%"))

    min_year = filters.get("min_year")
    if min_year is not None:
        stmt = stmt.where(Movie.year >= min_year)

    max_year = filters.get("max_year")
    if max_year is not None:
        stmt = stmt.where(Movie.year <= max_year)

    stmt = stmt.order_by(final_score.desc()).limit(top_k)

    return [
        {"movie": movie, "score": score}
        for movie, score in db.execute(stmt)
    ]
