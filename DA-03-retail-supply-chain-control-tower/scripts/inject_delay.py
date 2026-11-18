import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ct.db import execute, get_conn

ap = argparse.ArgumentParser()
ap.add_argument("--supplier", required=True)
ap.add_argument("--days", type=int, default=7)
ap.add_argument("--clear", action="store_true")
args = ap.parse_args()

conn = get_conn()
if args.clear:
    execute(conn, "UPDATE ops.delay_injection SET active = FALSE, updated_at = now() WHERE supplier_id = %s", (args.supplier,))
else:
    execute(conn, """INSERT INTO ops.delay_injection (supplier_id, extra_days, active) VALUES (%s, %s, TRUE)
                     ON CONFLICT (supplier_id) DO UPDATE SET extra_days = EXCLUDED.extra_days, active = TRUE,
                     updated_at = now()""", (args.supplier, args.days))
conn.commit()
print("cleared" if args.clear else f"{args.supplier} will be {args.days} days late from the next run")
