import sqlite3
conn = sqlite3.connect("data/shop.db")
print("Total sales:", conn.execute("SELECT COUNT(*) FROM sales").fetchone())
print("Top 3 products:")
for row in conn.execute("""SELECT p.name, SUM(s.quantity) AS total
                           FROM sales s JOIN products p ON p.id = s.product_id
                           GROUP BY p.name ORDER BY total DESC LIMIT 3"""):
    print(row)