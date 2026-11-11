# Routes for managing assessments

from flask import Blueprint, request, jsonify
from services import assessment_service


assessment_bp = Blueprint('assessment', __name__)

'''
A routing designed to render the assessment home page that
will contain all the assessments conducted with some statistics and summary information.
'''
@assessment_bp.route('/', methods=['GET'])
def assessment_index():
    return jsonify({"message": "Assessment index"})


'''
Route for retrieving all assessments stored in the database
The routing information will be passed as arguments in the query parameters that are part of the URL.
Example: /get-assessments?target_id=123 will return the assessments for the target with ID 123.
If no target id is provided, all assessments will be returned.
'''
@assessment_bp.route('/api/get-assessments', methods=['GET'])
def get_assessments():
    target_id = request.args.get("target_id")
    if target_id:
        assessments = assessment_service.get_assessments(target_id)
    else:
        assessments = assessment_service.get_all_assessments()
    return jsonify(assessments)

'''
Route for getting the assessment data by a given assessment ID.
The assessment ID will be provided as part of the URL path.
Example: /api/assessments/123 will return the assessment with ID 123.
'''
@assessment_bp.route('/api/assessments/<int:assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    assessment = assessment_service.get_assessment(assessment_id)
    return jsonify(assessment)


'''
Route for creating a new assessment.
The assessment data will be provided in the request body as JSON.
'''
@assessment_bp.route('/api/assessments', methods=['POST'])
def create_assessment():
    data = request.get_json()
    assessment = assessment_service.create_assessment(data)
    return jsonify(assessment), 201
