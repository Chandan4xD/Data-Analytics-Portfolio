from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from ct.db import get_conn
from ct.forecast import run_forecast


def forecast_task():
    conn = get_conn()
    try:
        return run_forecast(conn)
    finally:
        conn.close()


with DAG(
    dag_id="control_tower_forecast_daily",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["control-tower"],
) as dag:
    PythonOperator(task_id="forecast_demand", python_callable=forecast_task)
