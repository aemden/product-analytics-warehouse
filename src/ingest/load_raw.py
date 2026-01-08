import pathlib
import duckdb
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "data" / "raw"
DB = REPO_ROOT / "warehouse" / "analytics.duckdb"

def main():
    con = duckdb.connect(str(DB))

    users = pd.read_csv(RAW / "users.csv")
    events = pd.read_csv(RAW / "events.csv")
    orders = pd.read_csv(RAW / "orders.csv")
    ab = pd.read_csv(RAW / "ab_assignments.csv")

    con.execute("CREATE OR REPLACE TABLE raw_users AS SELECT * FROM users")
    con.execute("CREATE OR REPLACE TABLE raw_events AS SELECT * FROM events")
    con.execute("CREATE OR REPLACE TABLE raw_orders AS SELECT * FROM orders")
    con.execute("CREATE OR REPLACE TABLE raw_ab_assignments AS SELECT * FROM ab")

    print("Loaded tables into DuckDB:")
    print(con.execute("SHOW TABLES").df())

    con.close()
    print(f"DuckDB saved at: {DB}")

if __name__ == '__main__':
    main()
