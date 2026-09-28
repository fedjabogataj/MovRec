import json
from pathlib import Path
import numpy as np
from app.db import SessionLocal
from app.retrieval import search_movies
from .metrics import precision_at_k, recall_at_k, ndcg_at_k


queries_path = Path(__file__).parent / "queries.json"
K = 5
queries = json.load(open(queries_path))

metrics = []
with SessionLocal() as session:
    for query in queries:
        target = set(query["relevant_movie_ids"])
        results = search_movies(session, query["query"], K, query["filters"])
        ranked_ids = [r["movie"].id for r in results]

        row = [
            precision_at_k(ranked_ids, target, K),
            recall_at_k(ranked_ids, target, K),
            ndcg_at_k(ranked_ids, target, K),
        ]
        metrics.append(row)
        print(f"{query['query']:<40} precision={row[0]:.2f}  recall={row[1]:.2f}  ndcg={row[2]:.2f}")

metrics = np.array(metrics)
means = np.mean(metrics, axis=0)
print(f"{'AVERAGE':<40} precision={means[0]:.2f}  recall={means[1]:.2f}  ndcg={means[2]:.2f}")