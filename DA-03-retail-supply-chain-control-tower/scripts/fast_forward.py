import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ct import pipeline
from ct.db import get_conn

ap = argparse.ArgumentParser()
ap.add_argument("--cycles", type=int, default=30)
ap.add_argument("--step-hours", type=int, default=None)
args = ap.parse_args()

conn = get_conn()
for i in range(1, args.cycles + 1):
    anomalies, alerts_sent = pipeline.run_cycle(conn, args.step_hours)
    print(f"cycle {i}/{args.cycles}  sim_now={pipeline.sim_now(conn)}  anomalies={anomalies}  alerts={alerts_sent}")
