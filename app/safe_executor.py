import re
import sqlite3

DB_PATH = "data/shop.db"
MAX_ROWS = 200

FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create",
             "replace", "attach", "detach", "pragma", "vacuum", "truncate"]


class UnsafeSQLError(Exception):
    """Raised when a query is not a safe, read-only SELECT."""


def validate_sql(sql: str) -> str:
    """Return the cleaned SQL if it is safe, otherwise raise UnsafeSQLError."""
    sql = sql.strip().rstrip(";").strip()

    if not sql:
        raise UnsafeSQLError("Empty query.")

    # Block multiple statements, e.g. "SELECT ...; DROP TABLE ..."
    if ";" in sql:
        raise UnsafeSQLError("Only a single statement is allowed.")

    # Must start with SELECT (or WITH ... SELECT)
    if not re.match(r"^(select|with)\b", sql, flags=re.IGNORECASE):
        raise UnsafeSQLError("Only SELECT queries are allowed.")

    # Block dangerous keywords
    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", sql, flags=re.IGNORECASE):
            raise UnsafeSQLError(f"Forbidden keyword: {word.upper()}")

    return sql


def run_query(sql: str):
    """Validate and execute a query. Returns (columns, rows)."""
    safe_sql = validate_sql(sql)

    # Read-only connection: even if validation fails, the database cannot change
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cur = conn.execute(safe_sql)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchmany(MAX_ROWS)
        return columns, rows
    finally:
        conn.close()


if __name__ == "__main__":
    print(run_query("SELECT name, price FROM products LIMIT 3"))