
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
def get_all_assessments():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM assessments ORDER BY assessment_id;")
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
def new_assessment_validation(assessment_data):
    # Ensure the assessment_data contains the required fields
    if 'target_id' not in assessment_data:
        raise ValueError("assessment_data must contain 'target_id'")
    if 'test_type' not in assessment_data:
        raise ValueError("assessment_data must contain 'test_type'")
    if 'tcp_connectivity' in assessment_data['test_type'] and 'ports' not in assessment_data:
        raise ValueError("assessment_data must contain 'ports' for TCP connectivity tests")
    
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
def new_assessment(assessment_data):
    new_assessment_validation(assessment_data)

    newly_created_assessment_id = None
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO assessments (target_id)
                VALUES (%s)
                RETURNING assessment_id
            """, (assessment_data['target_id'],))
            newly_created_assessment_id = cursor.fetchone()['assessment_id']
            new_assessment_test(cursor, assessment_data, newly_created_assessment_id)

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
def new_assessment_test(cursor, assessment_data, expected_assessment_id):
    # Create a new entry for each of the test types requested
    for test_type in assessment_data['test_type']:
        cursor.execute("""
            INSERT INTO assessment_tests (assessment_id,test_type)
            VALUES (%s, %s)
        """, (
            expected_assessment_id, test_type))

        # If the test type is TCP connectivity, add the ports to the assessment_ports table
        if test_type == 'tcp_connectivity':
            new_port_testing(cursor, assessment_data, expected_assessment_id)


'''
This function adds the ports for a given assessment to the assessment_ports table.
The assessment_data should contain the 'ports' field which is a list of ports to be tested.
The expected_assessment_id is the ID of the assessment that was just created.
'''
def new_port_testing(cursor, assessment_data, expected_assessment_id):
    # For each port requesting to be tested, add it to the assessment_ports table
    for port in assessment_data['ports']:
        cursor.execute("""
            INSERT INTO assessment_ports (assessment_id, port)
            VALUES (%s, %s)
        """, (expected_assessment_id,port))