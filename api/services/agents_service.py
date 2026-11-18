
import os
import logging
import psycopg
from psycopg.rows import dict_row


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('psycopg').setLevel(logging.INFO)

'''
Connect to the database using psycopg
'''
def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        # Get the connection as a dictionary for ease of use
        row_factory=dict_row
    )

def get_all_agents():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    agent_id,
                    name,
                    location,
                    enabled,
                    last_seen_at,
                    created_at
                FROM agents
                ORDER BY agent_id;
            """)
            return cursor.fetchall()