import time, requests, pandas as pd, re
import os
from dotenv import load_dotenv
load_dotenv()

TMDB_API_KEY = os.environ["TMDB_API_KEY"]
TOP_N = 250



movies = pd.read_csv("./data/movies.csv")
links = pd.read_csv("./data/links.csv")
ratings = pd.read_csv("./data/ratings.csv")
tags = pd.read_csv("./data/tags.csv")



# joined = movies.merge(links, on="movieId")


# top_ids = ratings.groupby("movieId").size().sort_values(ascending=False).head(TOP_N).index

# subset = joined[joined["movieId"].isin(top_ids)]

# def split_title_year(raw_title:str) -> tuple[str, int | None]:
#     m = re.match(r"^(.*)\s\((\d{4})\)$", raw_title)
#     return (m.group(1), int(m.group(2))) if m else (raw_title, None)


# rows = []

# for _,row in subset.iterrows():
#     title, year = split_title_year(row["title"])
#     genres = row["genres"].replace("|",", ")
#     try:
#         resp = requests.get(f"https://api.themoviedb.org/3/movie/{int(row['tmdbId'])}",params={"api_key": TMDB_API_KEY})
#         resp.raise_for_status()
#         data = resp.json()
#         description = data.get("overview", "")
#         if not year and data.get("release_date"):
#             year = int(data["release_date"][:4])
#     except requests.RequestException as e:
#         print(f"skipping movieId={row['movieId']}: {e}")
#         continue
    
#     rows.append({"movieId": row["movieId"], "title": title, "year":year, "genres": genres, "description": description})
#     time.sleep(0.05)

# pd.DataFrame(rows).to_csv("./data/movies_enriched.csv", index=False)


movie_ratings = ratings.groupby("movieId")["rating"].agg(["count","mean"])
pd.DataFrame(movie_ratings).to_csv("./data/movie_ratings.csv")


