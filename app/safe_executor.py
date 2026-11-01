import re
import sqlite3

DB_PATH = "data/shop.db"
MAX_ROWS = 200

FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create",
             "replace", "attach", "detach", "pragma", "vacuum", "truncate"]


class UnsafeSQLError(Exception):
    pass


def validate_sql(sql: str) -> str:
    """SQL ko check karta hai. Safe ho to saaf shuda SQL wapas deta hai, warna error."""
    sql = sql.strip().rstrip(";").strip()

    if not sql:
        raise UnsafeSQLError("Khali SQL.")

    if ";" in sql:
        raise UnsafeSQLError("Sirf ek statement allow hai.")

    if not re.match(r"^(select|with)\b", sql, flags=re.IGNORECASE):
        raise UnsafeSQLError("Sirf SELECT queries allow hain.")

    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", sql, flags=re.IGNORECASE):
            raise UnsafeSQLError(f"Mana kiya gaya keyword: {word.upper()}")

    return sql


def run_query(sql: str):
    """Validate karke SQL chalata hai. (columns, rows) wapas deta hai."""
    safe_sql = validate_sql(sql)

    # Read-only connection: validation chook bhi jaye to database nahi badlega
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