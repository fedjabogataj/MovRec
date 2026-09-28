import math


def precision_at_k(ranked_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Of the top k returned ids, what fraction are relevant?"""
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for movie_id in top_k if movie_id in relevant_ids)
    return hits / len(top_k)


def recall_at_k(ranked_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Of all relevant ids, what fraction showed up in the top k?"""
    if not relevant_ids:
        return 0.0
    top_k = ranked_ids[:k]
    hits = sum(1 for movie_id in top_k if movie_id in relevant_ids)
    return hits / len(relevant_ids)


def _dcg(relevances: list[int]) -> float:
    # rank i (0-indexed) contributes rel_i / log2(rank + 1) = rel_i / log2(i + 2)
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def ndcg_at_k(ranked_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Like precision, but rewards relevant ids appearing higher in the ranking."""
    if not relevant_ids:
        return 0.0
    relevances = [1 if movie_id in relevant_ids else 0 for movie_id in ranked_ids[:k]]
    dcg = _dcg(relevances)
    # ideal ranking: every relevant item (up to k of them) ranked first
    ideal_relevances = [1] * min(k, len(relevant_ids))
    idcg = _dcg(ideal_relevances)
    return dcg / idcg if idcg > 0 else 0.0
