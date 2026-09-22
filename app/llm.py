import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Conversation, Message
from .retrieval import search_movies

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-flash-lite-latest"

SYSTEM_PROMPT = (
    "You are a movie recommendation assistant. When the user asks for a movie "
    "recommendation or wants to find a movie matching a description, genre, or era, "
    "call search_movies_tool to look up real movies from the catalog. Only recommend "
    "movies that come back from search_movies_tool's results — never invent a movie, "
    "its plot, or its year. If the tool returns no good matches, say so honestly "
    "instead of making something up."
)


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


def _make_search_tool(db: Session):
    def search_movies_tool(
        query: str,
        top_k: int = 5,
        genre: str | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> list[dict]:
        """Search the movie catalog by semantic meaning and optional filters.

        Use this whenever the user asks for a movie recommendation or wants to find
        a movie matching some description, genre, or year range.

        Args:
            query: A natural-language description of what kind of movie to find.
            top_k: How many results to return.
            genre: Optional genre filter, e.g. "Comedy".
            min_year: Optional minimum release year (inclusive).
            max_year: Optional maximum release year (inclusive).
        """
        results = search_movies(
            db, query, top_k=top_k,
            filters={"genre": genre, "min_year": min_year, "max_year": max_year},
        )
        return [
            {"title": r["movie"].title, "year": r["movie"].year,
             "genres": r["movie"].genres, "description": r["movie"].description}
            for r in results
        ]

    return search_movies_tool


def _send_message_with_retry(chat_session, user_message: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return chat_session.send_message(user_message)
        except errors.ServerError:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)


def chat(db: Session, conversation_id: int | None, user_message: str) -> tuple[int, str]:
    if conversation_id is None:
        conversation = Conversation()
        db.add(conversation)
        db.flush()
        conversation_id = conversation.id

    history_rows = db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).scalars().all()
    history = [
        types.Content(role=_to_gemini_role(m.role), parts=[types.Part.from_text(text=m.content)])
        for m in history_rows
    ]

    db.add(Message(conversation_id=conversation_id, role="user", content=user_message))
    db.commit()

    chat_session = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[_make_search_tool(db)],
        ),
        history=history,
    )
    response = _send_message_with_retry(chat_session, user_message)
    reply_text = response.text

    db.add(Message(conversation_id=conversation_id, role="assistant", content=reply_text))
    db.commit()

    return conversation_id, reply_text
