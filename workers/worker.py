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

def update_assessment_status(assessment_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                    UPDATE assessments
                    SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP
                    WHERE assessment_id = %s
                    AND status = 'running';
                    """, (assessment_id,))
            logging.info(f"Marked assessment {assessment_id} as completed")

def store_results(assessment_id, results):
    logging.info('Attempting to put results into assessment_results table')
    for test_type, data in results.items():
        with get_connection() as conn:
            with conn.cursor() as cursor:            
                cursor.execute("""
                    INSERT INTO assessment_results (assessment_id, test_type, metric_name, metric_value, unit, details)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (assessment_id, test_type, data[0]['metric_name'], data[0]['metric_value'], data[0]['unit'], json.dumps(data)))
                conn.commit()
            

    update_assessment_status(assessment_id)

while True:
    queuename, assessment_request = redisClient.brpop('assessment_queue', timeout=0)

    if assessment_request is None:
        continue

    if assessment_request:
        assessment_id = json.loads(assessment_request)['assessment_id']
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
                logging.info(f"Fetched assessment: {assessment}")

                results = {}

                if 'tcp_connectivity' in assessment['test_types']:
                    tcp_results = run_tcp_connectivity(assessment['target_ip'], assessment['ports'])
                    results['tcp_connectivity'] = tcp_results
                    logging.info(f"Ran TCP connectivity test for assessment {assessment['assessment_id']}")

                if 'latency' in assessment['test_types']:
                    latency_results = run_latency(assessment['target_ip'])
                    results['latency'] = latency_results
                    logging.info(f"Ran latency test for assessment {assessment['assessment_id']}")

                if 'throughput' in assessment['test_types']:
                    throughput_results = run_throughput(assessment['target_ip'])
                    results['throughput'] = throughput_results
                    logging.info(f"Ran throughput test for assessment {assessment['assessment_id']}")
                    
                if 'packetloss' in assessment['test_types']:
                    packetloss_results = run_packetloss(assessment['target_ip'])
                    results['packetloss'] = packetloss_results
                    logging.info(f"Ran packet loss test for assessment {assessment['assessment_id']}")

                # Store the combined results
                logging.info(f"Combined results for assessment {assessment['assessment_id']}: {results}")
                store_results(assessment['assessment_id'], results)
