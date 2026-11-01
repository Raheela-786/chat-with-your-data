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
    """Database ke tables aur columns ko text mein nikalta hai."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    conn.close()
    return "\n".join(r[0] for r in rows)


def clean_sql(text: str) -> str:
    """Agar model ne ```sql fences laga diye hon to hata deta hai."""
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
    return text.strip()


def generate_sql(question: str, retries: int = 3) -> str:
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
            # 503 jaisi temporary galti par dobara koshish
            if attempt == retries:
                raise
            wait = 2 * attempt
            print(f"Server busy ({e.code}), {wait}s baad dobara koshish...")
            time.sleep(wait)


if __name__ == "__main__":
    q = input("Sawal poochhein: ")
    print("\nGenerated SQL:\n", generate_sql(q))