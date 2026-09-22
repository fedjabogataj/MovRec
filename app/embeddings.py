import os, math, re, time

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def _l2_normalize(vector: list[float])-> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x/norm for x in vector]

def embed_texts(texts: list[str], task_type: str, max_retries: int = 5) -> list[list[float]]:
    for attempt in range(max_retries):
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=1536,
                ),
            )
            return [_l2_normalize(e.values) for e in result.embeddings]
        except errors.ClientError as e:
            if e.code !=429 or attempt == max_retries-1:
                raise
            delay = 65
            match = re.search(r"retry in ([\d.]+)s", str(e))
            if match:
                delay = float(match.group(1)) + 1
            print(f"rate limited, waiting {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
