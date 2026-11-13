import os
import logging
import psycopg
from psycopg.rows import dict_row
import redis
import json
from dotenv import load_dotenv
from assessments.tcp_connectivity import run_tcp_connectivity
from assessments.latency import run_latency
from assessments.throughput import run_throughput
from assessments.packetloss import run_packetloss


redisClient = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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


while True:
    result = redisClient.brpop('assessment_queue', timeout=5)

    if result is None:
        continue

    queuename, assessment_request = result
    
    if assessment_request:
        assessment_id = json.loads(assessment_request)['assessment_id']
        # Process the assessment here
        logging.info(f"Processing assessment {assessment_id}")
        

        # Get the assessment from the database:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE assessments
                    SET status = 'running',
                    started_at = CURRENT_TIMESTAMP
                    WHERE assessment_id = %s
                    AND status = 'pending'
                    RETURNING assessment_id;
                    """, (assessment_id,))

                claimed_assessment = cursor.fetchone()
                if not claimed_assessment:
                    logging.warning(f"Assessment {assessment_id} was not claimed, possibly already running.")
                    continue

                cursor.execute("""
                    SELECT
                        a.assessment_id,
                        a.status,
                        t.name AS target_name,
                        t.ip_address::text AS target_ip,

                        COALESCE(
                            (
                                SELECT ARRAY_AGG(at.test_type)
                                FROM assessment_tests at
                                WHERE at.assessment_id = a.assessment_id
                            ),
                            ARRAY[]::VARCHAR[]
                        ) AS test_types,

                        COALESCE(
                            (
                                SELECT ARRAY_AGG(ap.port)
                                FROM assessment_ports ap
                                WHERE ap.assessment_id = a.assessment_id
                            ),
                            ARRAY[]::INTEGER[]
                        ) AS ports

                    FROM assessments a
                    JOIN targets t ON a.target_id = t.target_id
                    WHERE a.assessment_id = %s;
                """, (assessment_id,))

                assessment = cursor.fetchone()

                if 'tcp_connectivity' in assessment['test_types']:
                    run_tcp_connectivity(assessment['target_ip'], assessment['ports'])
                if 'latency' in assessment['test_types']:
                    run_latency(assessment['target_ip'])
                if 'throughput' in assessment['test_types']:
                    run_throughput(assessment['target_ip'])
                if 'packetloss' in assessment['test_types']:
                    run_packetloss(assessment['target_ip'])

                logging.info(f"Fetched assessment: {assessment}")
