from .db import Base, engine, SessionLocal
import csv
from .models import Movie


Base.metadata.create_all(engine)

with SessionLocal() as session, open("data/movies_enriched.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        session.add(Movie(
            id = int(row["movieId"]),
            title=row["title"],
            year=int(row["year"]) if row["year"] else None,
            genres=row["genres"],
            description=row["description"],
        ))
    session.commit()
