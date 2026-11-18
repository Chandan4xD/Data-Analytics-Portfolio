import os

DSN = os.environ.get("CT_DSN", "postgresql://ct:ct@localhost:5432/control_tower")


SIM_STEP_HOURS = int(os.environ.get("CT_SIM_STEP_HOURS", "24"))

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")
ALERT_COOLDOWN_HOURS = int(os.environ.get("CT_ALERT_COOLDOWN_HOURS", "24"))


Z_THRESHOLD = float(os.environ.get("CT_Z_THRESHOLD", "3.0"))
Z_WINDOW = int(os.environ.get("CT_Z_WINDOW", "14"))
Z_MIN_POINTS = int(os.environ.get("CT_Z_MIN_POINTS", "7"))


MIN_DELTA_DELAY_DAYS = float(os.environ.get("CT_MIN_DELTA_DELAY_DAYS", "2.0"))
MIN_DELTA_DEMAND_UNITS = float(os.environ.get("CT_MIN_DELTA_DEMAND_UNITS", "5"))


STOCKOUT_RATE_MAX = float(os.environ.get("CT_STOCKOUT_RATE_MAX", "0.10"))
ON_TIME_MIN = float(os.environ.get("CT_ON_TIME_MIN", "0.80"))
DAYS_OF_INVENTORY_MIN = float(os.environ.get("CT_DOI_MIN", "7"))
