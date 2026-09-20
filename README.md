# MovRec

A small conversational movie recommender: a user asks for recommendations in plain language, the app retrieves relevant movies from a Postgres database via pgvector similarity search, and an LLM (OpenAI API) turns the retrieved results into a grounded, helpful reply. Built with FastAPI, and runs end to end in Docker.
