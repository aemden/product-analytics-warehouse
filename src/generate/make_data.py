import pathlib
import random
from datetime import datetime, timedelta

import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

def main():
    n_users = 5000
    start = datetime(2024, 10, 1)
    days = 60

    users = pd.DataFrame({
        "user_id": [f"u{i:05d}" for i in range(n_users)],
        "signup_dt": [start + timedelta(days=random.randint(0, days-1)) for _ in range(n_users)],
        "country": [random.choice(["US", "US", "US", "CA"]) for _ in range(n_users)],
        "device": [random.choice(["ios", "android", "web"]) for _ in range(n_users)],
    })

    # A/B assignment (sticky by user)
    assignments = users[["user_id"]].copy()
    assignments["experiment_id"] = "checkout_banner_v1"
    assignments["variant"] = assignments["user_id"].apply(lambda x: "treatment" if hash(x) % 2 == 0 else "control")
    assignments["assigned_dt"] = start

    events = []
    orders = []

    event_types = ["page_view", "add_to_cart", "purchase"]
    base_conv = {"control": 0.06, "treatment": 0.072}  # treatment lifts conversion

    for _, u in users.iterrows():
        variant = assignments.loc[assignments["user_id"] == u["user_id"], "variant"].iloc[0]
        # sessions per user
        n_sessions = max(1, int(random.gauss(3.5, 1.5)))
        for _s in range(n_sessions):
            session_dt = start + timedelta(days=random.randint(0, days-1), hours=random.randint(0, 23))
            session_id = f"s_{u['user_id']}_{int(session_dt.timestamp())}_{random.randint(100,999)}"

            # always at least one page view
            events.append([u["user_id"], session_id, session_dt, "page_view", None, None])

            # add_to_cart probability
            if random.random() < 0.25:
                dt2 = session_dt + timedelta(minutes=random.randint(1, 20))
                events.append([u["user_id"], session_id, dt2, "add_to_cart", None, None])

                # purchase probability depends on experiment variant
                if random.random() < base_conv[variant]:
                    dt3 = dt2 + timedelta(minutes=random.randint(1, 30))
                    order_id = f"o_{u['user_id']}_{int(dt3.timestamp())}_{random.randint(100,999)}"
                    revenue = round(max(5, random.gauss(65, 25)), 2)
                    events.append([u["user_id"], session_id, dt3, "purchase", order_id, revenue])
                    orders.append([order_id, u["user_id"], dt3, revenue])

    events_df = pd.DataFrame(events, columns=["user_id", "session_id", "event_ts", "event_type", "order_id", "revenue"])
    orders_df = pd.DataFrame(orders, columns=["order_id", "user_id", "order_ts", "revenue"])

    users.to_csv(OUT_DIR / "users.csv", index=False)
    assignments.to_csv(OUT_DIR / "ab_assignments.csv", index=False)
    events_df.to_csv(OUT_DIR / "events.csv", index=False)
    orders_df.to_csv(OUT_DIR / "orders.csv", index=False)

    print("Wrote:")
    print(" - data/raw/users.csv", len(users))
    print(" - data/raw/ab_assignments.csv", len(assignments))
    print(" - data/raw/events.csv", len(events_df))
    print(" - data/raw/orders.csv", len(orders_df))

if __name__ == "__main__":
    main()
