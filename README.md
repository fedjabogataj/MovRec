# MovRec

A small conversational movie recommender: a user asks for recommendations in plain language, the app retrieves relevant movies from a Postgres database via pgvector similarity search, and an LLM (Google's Gemini API) turns the retrieved results into a grounded, helpful reply. Built with FastAPI, and runs end to end in Docker.

Dataset: a 250-movie subset of MovieLens `ml-latest-small`, enriched with real plot summaries pulled from the TMDb API.

## Running it

```bash
cp .env.example .env   # then fill in GEMINI_API_KEY and TMDB_API_KEY
docker compose up --build
```

- `GET /health` — app + database reachability check
- `GET /movies?genre=...&min_year=...&max_year=...` — list/filter movies
- `GET /movies/{id}` — fetch one movie
- `POST /search` — semantic search directly (`{"query": "...", "top_k": 5}`)
- `POST /chat` — the conversational endpoint (`{"conversation_id": null, "message": "..."}`)

Interactive API docs: `http://localhost:8000/docs`.

## Example conversations

**Conversation 1 — a request, then a follow-up that needs memory, not a new search**

> **User:** Can you recommend a mind-bending sci-fi movie?
>
> **Assistant:** Here are a few mind-bending sci-fi (and sci-fi-adjacent) recommendations from the catalog:
>
> 1. **Eternal Sunshine of the Spotless Mind** (2004) – *Drama, Romance, Sci-Fi* — After a bitter breakup, a man discovers that his ex-girlfriend has undergone a medical procedure to erase all memories of him from her mind. He decides to undergo the same process, but as his memories fade, he begins to regret it and tries to hide her away in the corners of his subconscious.
> 2. **Donnie Darko** (2001) – *Drama, Mystery, Sci-Fi, Thriller* — After narrowly surviving a freak accident involving a jet engine falling into his bedroom, a troubled teenager is plagued by visions of a sinister man in a rabbit suit who pushes him into committing bizarre, reality-altering acts.
> 3. **Twelve Monkeys** (1995) – *Mystery, Sci-Fi, Thriller* — Set in a devastated future where a lethal virus has driven humanity underground, a convict is sent back in time to gather information about the virus's origin.
> 4. **The Prestige** (2006) – *Drama, Mystery, Sci-Fi, Thriller* — Two rival magicians engage in a bitter, lifelong battle for supremacy, escalating to dangerous and reality-bending extremes.
>
> **User:** Which of those did you mention has Jim Carrey in it?
>
> **Assistant:** **Eternal Sunshine of the Spotless Mind** (2004) stars Jim Carrey as Joel Barish, alongside Kate Winslet.

The second turn answered correctly from conversation memory *without* triggering a new catalog search — the model recognized this was answerable from what it had already said.

**Conversation 2 — genre + era filtering**

> **User:** Recommend a good comedy from the 90s
>
> **Assistant:** Here are a few great comedy recommendations from the 1990s:
> - **Liar Liar** (1997) – Starring Jim Carrey at the peak of his physical comedy powers as a fast-talking lawyer who is mysteriously forced to tell the absolute truth for 24 hours.
> - **Happy Gilmore** (1996) – A hilarious sports comedy starring Adam Sandler as a hockey player with a fiery temper who brings his explosive slap-shot swing to the professional golf tour.
> - **The Birdcage** (1996) – A brilliant, fast-paced farce starring Robin Williams and Nathan Lane.
> - **There's Something About Mary** (1998) – A wild romantic comedy starring Ben Stiller and Cameron Diaz.
> - **Fargo** (1996) – A darkly funny crime-comedy directed by the Coen brothers.

**Conversation 3 — open-ended genre request**

> **User:** Suggest a good horror movie
>
> **Assistant:** Here are a few great horror movies you can check out, depending on what kind of scare you're in the mood for:
> 1. **The Shining** (1980) – A psychological masterpiece about a family isolated in a snowbound hotel where the father slowly descends into murderous madness.
> 2. **Alien** (1979) – A tense, claustrophobic sci-fi horror about a spaceship crew hunted by a terrifying extraterrestrial organism.
> 3. **Psycho** (1960) – Alfred Hitchcock's classic thriller/horror about a woman on the run who checks into the infamous Bates Motel.
> 4. **Jaws** (1975) – A suspenseful thriller-horror about a beach community terrorized by a massive great white shark.
> 5. **Shaun of the Dead** (2004) – A clever horror-comedy about an unambitious bloke trying to win back his ex while navigating a sudden zombie apocalypse.

Every recommendation above is a real row from the seeded Postgres catalog, retrieved by the `search_movies_tool` the LLM calls — not invented by the model.

## 60-second architecture explanation

> A user sends a message to `POST /chat`. FastAPI saves it to Postgres in a `messages` table, then loads that conversation's prior turns and hands the whole history to Gemini, along with a system prompt and one tool the model can call: `search_movies_tool`.
>
> If the user's message calls for a recommendation, Gemini decides on its own to call that tool with a natural-language query plus any genre/year filters it inferred. The tool embeds that query text using Gemini's embedding API, then runs a cosine-distance search against a `pgvector` column in Postgres holding a pre-computed embedding for every movie in the catalog — so retrieval is a real nearest-neighbor search over vector representations of plot/genre/title, not a keyword match. The tool returns the top matches as plain data — titles, years, genres, descriptions — back to the model.
>
> Gemini then writes a final natural-language reply grounded in *only* those retrieved movies — the system prompt explicitly forbids inventing a movie or its plot. That reply gets saved back to Postgres and returned to the user. The whole thing — FastAPI, Postgres/pgvector, and the app itself — runs as two containers via Docker Compose, so it starts and behaves the same way anywhere.
>
> Where each piece fits: **FastAPI** is the HTTP layer and request/response validation. **Postgres** holds both the movie catalog (with embeddings) and the conversation history — one database, two jobs. **pgvector** is what makes "semantic search" possible at all — it's the extension that lets Postgres do vector similarity search natively. **TMDb** was a one-time, offline enrichment step: MovieLens has no plot text, so real summaries were pulled from TMDb before anything else happened. **Gemini** does two distinct jobs — one model call embeds text into vectors (retrieval), a separate model call reasons about the conversation and decides when to search and how to phrase the final answer (generation).
