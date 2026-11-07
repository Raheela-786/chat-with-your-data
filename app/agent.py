import os
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from dotenv import load_dotenv

from app.sql_generator import get_schema, clean_sql
from app.safe_executor import run_query

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MAX_ATTEMPTS = 3


def build_system_prompt() -> str:
    return f"""You are an expert SQLite analyst.
Write ONE SQLite SELECT query that answers the user's question.

Rules:
- Output ONLY the SQL query, no explanation, no markdown fences.
- Use only tables and columns that exist in the schema.
- Only SELECT statements.
- Dates are stored as text in YYYY-MM-DD format.
- Revenue = sales.quantity * products.price.
- If the question cannot be answered from the schema, output exactly: CANNOT_ANSWER

Schema:
{get_schema()}
"""


def ask_llm(messages: list, retries: int = 5) -> str:
    """Call the LLM, retrying on temporary server errors."""
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=build_system_prompt(),
                    temperature=0,
                ),
            )
            return clean_sql(response.text)
        except ServerError:
            if attempt == retries:
                raise
            time.sleep(5 * attempt)


def answer_question(question: str) -> dict:
    """Generate SQL, run it safely, and self-correct if it fails."""
    messages = [types.Content(role="user", parts=[types.Part(text=question)])]
    history = []

    for attempt in range(1, MAX_ATTEMPTS + 1):
        sql = ask_llm(messages)

        if sql.strip().upper() == "CANNOT_ANSWER":
            return {"ok": False, "sql": "", "columns": [], "rows": [],
                    "attempts": history,
                    "message": "This question cannot be answered from the database."}

        try:
            columns, rows = run_query(sql)
            history.append({"attempt": attempt, "sql": sql, "error": None})
            return {"ok": True, "sql": sql, "columns": columns,
                    "rows": rows, "attempts": history}
        except Exception as e:
            history.append({"attempt": attempt, "sql": sql, "error": str(e)})
            # Show the model its own error and ask it to fix the query
            messages.append(types.Content(role="model", parts=[types.Part(text=sql)]))
            messages.append(types.Content(role="user", parts=[types.Part(
                text=f"That SQL failed with error: {e}\nFix it. Output ONLY the corrected SQL.")]))

    return {"ok": False, "sql": sql, "columns": [], "rows": [],
            "attempts": history,
            "message": "Could not produce a working query."}


if __name__ == "__main__":
    q = input("Ask a question: ")
    result = answer_question(q)
    for h in result["attempts"]:
        print(f"Attempt {h['attempt']}: {h['sql']}")
        if h["error"]:
            print("   Error:", h["error"])
    if result["ok"]:
        print("\nColumns:", result["columns"])
        for row in result["rows"]:
            print(row)
    else:
        print("\n", result.get("message", "No answer found."))