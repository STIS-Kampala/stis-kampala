import os
import psycopg2

def get_conn():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=5432,
        sslmode="require"
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            road_id TEXT,
            road_name TEXT,
            label TEXT,
            delay_ratio FLOAT,
            hour INT,
            rain_mm FLOAT,
            model_used TEXT,
            source TEXT DEFAULT 'api'
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
