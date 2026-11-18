
import os
import logging
import psycopg
from psycopg.rows import dict_row
import redis
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('psycopg').setLevel(logging.INFO)

redisClient = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"), 
    port=int(os.getenv("REDIS_PORT", 6379)), 
    db=0, decode_responses=True
)
redisListName = 'assessment_queue'


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


'''
Get a single assessment using the assessment_id
'''
def get_assessment(assessment_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT * 
            FROM assessments
            WHERE assessment_id = %s;
            """,(assessment_id,))

            return cursor.fetchone()


'''
Validate the data for a new assessment before inserting it into the database
'''
def create_assessment_validation(assessment_data):
    # Ensure the assessment_data contains the required fields
    if 'target_id' not in assessment_data:
        raise ValueError("assessment_data must contain 'target_id'")
    if 'test_type' not in assessment_data:
        raise ValueError("assessment_data must contain 'test_type'")
    if 'tcp_connectivity' in assessment_data['test_type'] and 'ports' not in assessment_data:
        raise ValueError("assessment_data must contain 'ports' for TCP connectivity tests")
    if 'agent_id' not in assessment_data:
        raise ValueError("assessment_data must contain 'agent_id'")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT agent_id
                FROM agents
                WHERE agent_id = %s
                AND enabled = TRUE;
            """, (assessment_data['agent_id'],))

            if not cursor.fetchone():
                raise ValueError("agent_id must reference a valid enabled agent")
    
    # Make sure target_id references a valid available target
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT target_id FROM targets WHERE target_id = %s;", (assessment_data['target_id'],))
            if not cursor.fetchone():
                raise ValueError("target_id must reference a valid target")
    
    # test_type should not be empty and should be a list of valid test types
    if not assessment_data['test_type']:
        raise ValueError("test_type must not be empty")
    valid_test_types = ['tcp_connectivity', 'latency', 'throughput', 'packet_loss']
    for test_type in assessment_data['test_type']:
        if test_type not in valid_test_types:
            raise ValueError(f"Invalid test_type: {test_type}")
    
    # If tcp_connectivity is in the test_type list, ensure ports are provided and between 1 & 65535
    # Make sure if tcp_connectivity is a test_type, there are no duplicate ports
    if 'tcp_connectivity' in assessment_data['test_type']:
        ports = assessment_data.get('ports', [])
        if not ports:
            raise ValueError("ports must be provided for TCP connectivity tests")
        for port in ports:
            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError(f"Invalid port: {port}")
        if len(ports) != len(set(ports)):
            raise ValueError("Duplicate ports are not allowed for TCP connectivity tests")
    
    # Make sure the test_type list does not contain duplicates
    if len(assessment_data['test_type']) != len(set(assessment_data['test_type'])):
        raise ValueError("Duplicate test types are not allowed")

'''
Add a new assessment to the database
When creating a new assessment, assessment_data should contain:
- target_id [References the id for the given target]
- test_type [List of types of tests to be performed]
- ports [List of ports to be tested for TCP connectivity]
'''
def create_assessment(assessment_data):
    create_assessment_validation(assessment_data)

    newly_created_assessment_id = None

    with get_connection() as conn:
        with conn.cursor() as cursor:

            # Retrieve the selected agent's location
            cursor.execute("""
                SELECT location
                FROM agents
                WHERE agent_id = %s
                AND enabled = TRUE;
            """, (assessment_data['agent_id'],))

            agent = cursor.fetchone()

            if not agent or not agent['location']:
                raise ValueError("Selected agent is unavailable")

            # Create the assessment
            cursor.execute("""
                INSERT INTO assessments (target_id, agent_id)
                VALUES (%s, %s)
                RETURNING assessment_id;
            """, (
                assessment_data['target_id'],
                assessment_data['agent_id']
            ))

            newly_created_assessment_id = cursor.fetchone()['assessment_id']

            # Add configured tests and ports
            create_assessment_test(
                cursor,
                assessment_data,
                newly_created_assessment_id
            )

    # Route the job to the selected agent's regional queue
    queue_name = f"assessment_queue:{agent['location']}"

    job = {
        "assessment_id": newly_created_assessment_id
    }

    redisClient.lpush(queue_name, json.dumps(job))

    return newly_created_assessment_id

'''
Helper function for when a new assessment is created
This function will add the specific type of assessment to the assessment_tests table
The assessment_data should contain the 'test_type' field which should be one of the following:
- tcp_connectivity
- latency
- throughput
- packet_loss
The expected_assessment_id is the ID that was just created when the assessment was requested by a user
and input into the assessments table
'''
def create_assessment_test(cursor, assessment_data, expected_assessment_id):
    # Create a new entry for each of the test types requested
    for test_type in assessment_data['test_type']:
        cursor.execute("""
            INSERT INTO assessment_tests (assessment_id,test_type)
            VALUES (%s, %s)
        """, (
            expected_assessment_id, test_type))

        # If the test type is TCP connectivity, add the ports to the assessment_ports table
        if test_type == 'tcp_connectivity':
            create_port_testing(cursor, assessment_data, expected_assessment_id)


'''
This function adds the ports for a given assessment to the assessment_ports table.
The assessment_data should contain the 'ports' field which is a list of ports to be tested.
The expected_assessment_id is the ID of the assessment that was just created.
'''
def create_port_testing(cursor, assessment_data, expected_assessment_id):
    # For each port requesting to be tested, add it to the assessment_ports table
    for port in assessment_data['ports']:
        cursor.execute("""
            INSERT INTO assessment_ports (assessment_id, port)
            VALUES (%s, %s)
        """, (expected_assessment_id,port))

'''
This function updates an existing assessment in the database.
The assessment_id is the ID of the assessment to be updated.
The assessment_data contains the new data for the assessment, including the 'target_id' field.
The function returns the updated assessment ID.
'''
def update_assessment(assessment_id, assessment_data):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE assessments
                SET target_id = %s
                WHERE assessment_id = %s
                RETURNING assessment_id
            """, (assessment_data['target_id'], assessment_id))
            updated_assessment_id = cursor.fetchone()['assessment_id']
            return updated_assessment_id


'''
This function willretrieve an assessment and all its associated results from the database.
The assessment_id is the ID of the assessment to be retrieved.
The function returns a dictionary containing the assessment and its results.
'''
def get_assessment_details(assessment_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:

            # Retrieve assessment information
            cursor.execute("""
                SELECT
                    a.assessment_id,
                    a.status,
                    a.created_at,
                    a.started_at,
                    a.completed_at,
                    a.error_message,

                    t.target_id,
                    t.name AS target_name,
                    host(t.ip_address) AS ip_address,
                    t.location AS target_location,
                    t.description AS target_description,

                    ag.agent_id,
                    ag.name AS agent_name,
                    ag.location AS agent_location,
                    ag.last_seen_at

                FROM assessments a
                JOIN targets t
                    ON a.target_id = t.target_id
                LEFT JOIN agents ag
                    ON a.agent_id = ag.agent_id

                WHERE a.assessment_id = %s
            """, (assessment_id,))

            assessment = cursor.fetchone()

            # Assessment does not exist
            if not assessment:
                return None

            # Retrieve configured tests
            cursor.execute("""
                SELECT test_type
                FROM assessment_tests
                WHERE assessment_id = %s
                ORDER BY test_type
            """, (assessment_id,))

            tests = cursor.fetchall()

            # Retrieve configured ports
            cursor.execute("""
                SELECT port
                FROM assessment_ports
                WHERE assessment_id = %s
                ORDER BY port
            """, (assessment_id,))

            ports = cursor.fetchall()

            # Retrieve assessment results
            cursor.execute("""
                SELECT
                    result_id,
                    port,
                    test_type,
                    metric_name,
                    metric_value,
                    unit,
                    details,
                    measured_at
                FROM assessment_results
                WHERE assessment_id = %s
                ORDER BY measured_at
            """, (assessment_id,))

            results = cursor.fetchall()

            # Add configuration information to assessment
            assessment['tests'] = tests
            assessment['ports'] = ports

            return {
                'assessment': assessment,
                'results': results
            }

def get_all_agents():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    agent_id,
                    name,
                    location
                FROM agents
                WHERE enabled = TRUE
                ORDER BY location;
            """)

            return cursor.fetchall()