import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.safe_executor import validate_sql, run_query, UnsafeSQLError


def test_select_allowed():
    assert validate_sql("SELECT * FROM products") == "SELECT * FROM products"


def test_trailing_semicolon_ok():
    assert validate_sql("SELECT 1;") == "SELECT 1"


@pytest.mark.parametrize("bad", [
    "DROP TABLE sales",
    "DELETE FROM sales",
    "UPDATE products SET price = 0",
    "INSERT INTO products(name) VALUES ('x')",
    "SELECT 1; DROP TABLE sales",
    "ALTER TABLE sales ADD COLUMN x INT",
    "PRAGMA table_info(sales)",
    "",
])
def test_dangerous_blocked(bad):
    with pytest.raises(UnsafeSQLError):
        validate_sql(bad)


def test_run_query_works():
    cols, rows = run_query("SELECT name FROM products LIMIT 2")
    assert cols == ["name"]
    assert len(rows) == 2