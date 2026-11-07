import os
import re
import time
import sqlite3
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DB_PATH = "data/shop.db"
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


def get_schema() -> str:
    """Return the CREATE TABLE statements of the database as text."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    conn.close()
    return "\n".join(r[0] for r in rows)


def clean_sql(text: str) -> str:
    """Remove markdown code fences if the model added them."""
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
    return text.strip()


def generate_sql(question: str, retries: int = 5) -> str:
    """Ask the LLM to translate a natural-language question into SQL."""
    schema = get_schema()
    system_prompt = f"""You are an expert SQLite analyst.
Given the database schema below, write ONE SQLite SELECT query that answers the user's question.

Rules:
- Output ONLY the SQL query, no explanation, no markdown fences.
- Use only tables and columns that exist in the schema.
- Only SELECT statements. Never INSERT, UPDATE, DELETE, DROP, or ALTER.
- Dates are stored as text in YYYY-MM-DD format.
- Revenue = sales.quantity * products.price.

Schema:
{schema}
"""
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0,
                ),
            )
            return clean_sql(response.text)
        except ServerError as e:
            # Retry on temporary server errors such as 503
            if attempt == retries:
                raise
            wait = 5 * attempt
            print(f"Server busy ({e.code}), retrying in {wait}s...")
            time.sleep(wait)


if __name__ == "__main__":
    q = input("Ask a question: ")
    print("\nGenerated SQL:\n", generate_sql(q))