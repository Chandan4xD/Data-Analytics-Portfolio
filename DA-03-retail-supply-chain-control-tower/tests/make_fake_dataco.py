import sys

import numpy as np
import pandas as pd

out = sys.argv[1] if len(sys.argv) > 1 else "data/fake_dataco.csv"
rng = np.random.default_rng(7)
n_products, days = 40, 120
cats = ["Cleats", "Fishing", "Camping", "Cardio", "Water Sports", "Shoes"]
rows, item_id = [], 1
for d in range(days):
    day = pd.Timestamp("2017-01-01") + pd.Timedelta(days=d)
    for _ in range(int(rng.poisson(45))):
        pid = int(rng.integers(1000, 1000 + n_products))
        ts = day + pd.Timedelta(minutes=int(rng.integers(0, 1440)))
        sched = int(rng.choice([2, 3, 4]))
        real = max(0, sched + int(rng.choice([-1, 0, 0, 0, 1, 2])))
        price = 10 + (pid % 7) * 12
        qty = int(rng.integers(1, 4))
        rows.append({
            "Order Item Id": item_id, "Order Id": item_id // 2,
            "order date (DateOrders)": ts.strftime("%m/%d/%Y %H:%M"),
            "shipping date (DateOrders)": (ts + pd.Timedelta(hours=int(rng.integers(0, 30)))).strftime("%m/%d/%Y %H:%M"),
            "Product Card Id": pid, "Product Name": f"Product {pid}", "Category Name": cats[pid % len(cats)],
            "Order Item Quantity": qty, "Order Item Total": price * qty, "Order Item Product Price": price,
            "Days for shipping (real)": real, "Days for shipment (scheduled)": sched,
            "Delivery Status": "Late delivery" if real > sched else "Advance shipping",
        })
        item_id += 1
pd.DataFrame(rows).to_csv(out, index=False, encoding="latin-1")
print(f"wrote {len(rows)} fake rows to {out}")
