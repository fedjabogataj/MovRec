from .db import SessionLocal
from .models import MovieRating
from .stats import compute_bayesian_averages


with SessionLocal() as session:
    movie_ratings = session.query(MovieRating).all()
    triples = [(r.id, r.count, r.mean) for r in movie_ratings]
    scores = compute_bayesian_averages(triples)
    for rating in movie_ratings:
        rating.bayesian_avg = scores[rating.id]

    session.commit()