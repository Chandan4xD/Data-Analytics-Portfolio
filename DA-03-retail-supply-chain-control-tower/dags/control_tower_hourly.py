from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from ct import pipeline, whatif
from ct.db import get_conn


def with_conn(fn):
    def task():
        conn = get_conn()
        try:
            return fn(conn)
        finally:
            conn.close()
    return task


with DAG(
    dag_id="control_tower_hourly",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["control-tower"],
) as dag:
    steps = [
        ("replay_orders", pipeline.replay_orders),
        ("update_inventory", pipeline.update_inventory),
        ("compute_kpis", pipeline.compute_kpis),
        ("refresh_whatif_scenarios", whatif.refresh_scenarios),
        ("detect_anomalies", pipeline.detect_anomalies),
        ("send_alerts", pipeline.send_alerts),
        ("data_quality_checks", pipeline.run_dq),
    ]
    tasks = [PythonOperator(task_id=name, python_callable=with_conn(fn)) for name, fn in steps]
    for upstream, downstream in zip(tasks, tasks[1:]):
        upstream >> downstream
