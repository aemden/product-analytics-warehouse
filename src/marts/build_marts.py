import pathlib
import duckdb

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = REPO_ROOT / "warehouse" / "analytics.duckdb"

def main():
    con = duckdb.connect(str(DB))

    # Clean / typed events
    con.execute("""
    CREATE OR REPLACE TABLE fct_events AS
    SELECT
      user_id,
      session_id,
      CAST(event_ts AS TIMESTAMP) AS event_ts,
      event_type,
      order_id,
      CAST(revenue AS DOUBLE) AS revenue
    FROM raw_events
    """)

    con.execute("""
    CREATE OR REPLACE TABLE dim_user AS
    SELECT
      user_id,
      CAST(signup_dt AS TIMESTAMP) AS signup_dt,
      country,
      device
    FROM raw_users
    """)

    con.execute("""
    CREATE OR REPLACE TABLE fct_orders AS
    SELECT
      order_id,
      user_id,
      CAST(order_ts AS TIMESTAMP) AS order_ts,
      CAST(revenue AS DOUBLE) AS revenue
    FROM raw_orders
    """)

    # Sessions: one row per session with whether it converted
    con.execute("""
    CREATE OR REPLACE TABLE fct_sessions AS
    SELECT
      session_id,
      user_id,
      MIN(event_ts) AS session_start_ts,
      MAX(event_ts) AS session_end_ts,
      SUM(CASE WHEN event_type='page_view' THEN 1 ELSE 0 END) AS page_views,
      SUM(CASE WHEN event_type='add_to_cart' THEN 1 ELSE 0 END) AS add_to_cart_events,
      SUM(CASE WHEN event_type='purchase' THEN 1 ELSE 0 END) AS purchases,
      MAX(CASE WHEN event_type='purchase' THEN 1 ELSE 0 END) AS converted
    FROM fct_events
    GROUP BY 1,2
    """)

    # Funnel daily counts
    con.execute("""
    CREATE OR REPLACE TABLE fct_funnel_daily AS
    SELECT
      CAST(event_ts AS DATE) AS event_date,
      COUNT(DISTINCT CASE WHEN event_type='page_view' THEN session_id END) AS sessions_with_page_view,
      COUNT(DISTINCT CASE WHEN event_type='add_to_cart' THEN session_id END) AS sessions_with_add_to_cart,
      COUNT(DISTINCT CASE WHEN event_type='purchase' THEN session_id END) AS sessions_with_purchase
    FROM fct_events
    GROUP BY 1
    ORDER BY 1
    """)

    # A/B results: conversion by variant (session-level)
    con.execute("""
    CREATE OR REPLACE TABLE ab_results AS
    SELECT
      a.experiment_id,
      a.variant,
      COUNT(DISTINCT s.session_id) AS sessions,
      SUM(s.converted) AS conversions,
      (SUM(s.converted) * 1.0) / NULLIF(COUNT(DISTINCT s.session_id), 0) AS conversion_rate
    FROM raw_ab_assignments a
    JOIN fct_sessions s USING(user_id)
    GROUP BY 1,2
    ORDER BY 1,2
    """)

    print("Built marts. Tables now:")
    print(con.execute("SHOW TABLES").df())

    print("\nA/B results:")
    print(con.execute("SELECT * FROM ab_results").df())

    con.close()

if __name__ == "__main__":
    main()
