from .db import Base, engine, SessionLocal
import csv
from .models import Movie
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
