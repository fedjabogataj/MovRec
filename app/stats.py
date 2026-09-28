import numpy as np




def compute_bayesian_averages(rows: list[tuple[int,int,float]], m=None) -> dict[int, float]:
    movie_ids, counts, means = zip(*rows)
    counts = np.array(counts)
    means = np.array(means)

    C = np.average(means, weights=counts)   # global mean, weighted by how many ratings back each mean
    if m is None:
        m = np.median(counts)                # smoothing constant — "typical" rating count

    bayesian = (counts / (counts + m)) * means + (m / (counts + m)) * C
    return {movie_id: float(value) for movie_id, value in zip(movie_ids, bayesian)}