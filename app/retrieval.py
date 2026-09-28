import numpy as np
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .embeddings import embed_texts
from .models import Movie, MovieRating



ALPHA = 0.8          # weight on semantic similarity vs. popularity
RATING_MIN, RATING_MAX = 0.5, 5.0   # MovieLens rating scale
MMR_LAMBDA = 0.7      # weight on relevance vs. diversity in re-ranking
OVERFETCH_FACTOR = 4  # candidate pool size = top_k * this, so MMR has room to diversify


def mmr_rerank(candidates: list[dict], top_k: int, lambda_param: float = MMR_LAMBDA) -> list[dict]:
    """Greedily pick top_k candidates, trading a little relevance for dissimilarity to picks already made."""
    if not candidates:
        return []

    embeddings = np.array([c["movie"].embedding for c in candidates])
    embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)

    remaining = list(range(len(candidates)))
    selected: list[int] = []

    while remaining and len(selected) < top_k:
        def mmr_score(i):
            relevance = candidates[i]["score"]
            if not selected:
                return relevance
            redundancy = max(embeddings[i] @ embeddings[j] for j in selected)
            return lambda_param * relevance - (1 - lambda_param) * redundancy

        best = max(remaining, key=mmr_score)
        selected.append(best)
        remaining.remove(best)

    return [candidates[i] for i in selected]


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

    stmt = stmt.order_by(final_score.desc()).limit(top_k * OVERFETCH_FACTOR)

    candidates = [
        {"movie": movie, "score": score}
        for movie, score in db.execute(stmt)
    ]

    return mmr_rerank(candidates, top_k)
