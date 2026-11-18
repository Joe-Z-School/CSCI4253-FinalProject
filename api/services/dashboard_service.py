
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


'''
Get all the assessments from the database
'''
def get_all_assessments(target_id=None):
    query = """
            SELECT
                a.assessment_id,
                a.target_id,
                t.name AS target_name,
                host(t.ip_address) AS target_ip,
                a.agent_id,
                ag.name AS agent_name,
                a.status,
                a.created_at,
                a.started_at,
                a.completed_at,
                a.error_message,
    
                COALESCE(
                    (
                        SELECT ARRAY_AGG(at.test_type ORDER BY at.test_type)
                        FROM assessment_tests at
                        WHERE at.assessment_id = a.assessment_id
                    ),
                    ARRAY[]::VARCHAR[]
                ) AS test_types,
    
                COALESCE(
                    (
                        SELECT ARRAY_AGG(ap.port ORDER BY ap.port)
                        FROM assessment_ports ap
                        WHERE ap.assessment_id = a.assessment_id
                    ),
                    ARRAY[]::INTEGER[]
                ) AS ports
    
            FROM assessments a
            JOIN targets t ON a.target_id = t.target_id
            LEFT JOIN agents ag ON a.agent_id = ag.agent_id
        """
    
    params = []
    
    if target_id is not None:
        query += " WHERE a.target_id = %s"
        params.append(target_id)

    query += " ORDER BY a.created_at DESC;"
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

