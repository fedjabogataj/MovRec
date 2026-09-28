from .db import Base, engine, SessionLocal
import csv
from .models import Movie, MovieRating
from .embeddings import embed_texts


Base.metadata.create_all(engine)

BATCH_SIZE = 75

rows = list(csv.DictReader(open("data/movies_enriched.csv")))
passages = [
    f"{row['title']} ({row['year']}). Genres: {row['genres']}. {row['description']}"
    for row in rows
]

embeddings = []
for i in range(0, len(passages), BATCH_SIZE):
    batch = passages[i:i + BATCH_SIZE]
    embeddings.extend(embed_texts(batch, task_type="RETRIEVAL_DOCUMENT"))

with SessionLocal() as session:
    for row, embedding in zip(rows, embeddings):
        session.add(Movie(
            id=int(row["movieId"]),
            title=row["title"],
            year=int(row["year"]) if row["year"] else None,
            genres=row["genres"],
            description=row["description"],
            embedding=embedding,
        ))
    session.commit()

seeded_movie_ids = {int(row["movieId"]) for row in rows}

movie_ratings = [
    row for row in csv.DictReader(open("data/movie_ratings.csv"))
    if int(row["movieId"]) in seeded_movie_ids
]

with SessionLocal() as session:
    for movie in movie_ratings:
        session.add(MovieRating(
            id = int(movie['movieId']),
            count = int(movie['count']),
            mean = float(movie['mean']),
        ))
    session.commit()