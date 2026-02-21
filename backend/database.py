# database.py
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'sslmode': 'require'
}

connection_pool = None

def init_pool():
    global connection_pool
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **db_config)

def get_db():
    global connection_pool
    if connection_pool is None:
        init_pool()
    return connection_pool.getconn()

def close_connection(conn):
    global connection_pool
    if conn:
        connection_pool.putconn(conn)

def get_db_cursor():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor