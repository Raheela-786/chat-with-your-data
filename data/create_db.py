import sqlite3, random
from datetime import date, timedelta

conn = sqlite3.connect("data/shop.db")
c = conn.cursor()
c.executescript("""
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
CREATE TABLE sales(id INTEGER PRIMARY KEY, customer_id INT, product_id INT,
                   quantity INT, sale_date TEXT);
""")

cities = ["Lahore", "Karachi", "Multan", "Faisalabad", "Islamabad"]
products = [("Rice 5kg","Grocery",1500),("Wheat Flour 10kg","Grocery",1800),
            ("Cooking Oil 5L","Grocery",3200),("Tea 1kg","Grocery",1400),
            ("Headphones","Electronics",2500),("Power Bank","Electronics",3500),
            ("T-Shirt","Clothing",1200),("Jeans","Clothing",3000)]
c.executemany("INSERT INTO products(name,category,price) VALUES(?,?,?)", products)
for i in range(1, 51):
    c.execute("INSERT INTO customers(name,city) VALUES(?,?)",
              (f"Customer {i}", random.choice(cities)))
start = date.today() - timedelta(days=180)
for _ in range(1000):
    d = start + timedelta(days=random.randint(0, 180))
    c.execute("INSERT INTO sales(customer_id,product_id,quantity,sale_date) VALUES(?,?,?,?)",
              (random.randint(1,50), random.randint(1,8), random.randint(1,5), d.isoformat()))
conn.commit(); conn.close()
print("Database ready!")