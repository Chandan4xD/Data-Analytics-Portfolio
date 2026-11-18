import pandas as pd
import psycopg2
from .config import DSN


def get_conn():
    return psycopg2.connect(DSN)


def read_df(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)


def execute(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
