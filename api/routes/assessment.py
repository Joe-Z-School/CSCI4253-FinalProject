# Routes for managing assessments

from flask import Blueprint, request, jsonify, render_template
from services import assessment_service


assessment_bp = Blueprint('assessment', __name__)


# ==========================================
# HTML Page Rendering Routes
# ==========================================

'''
A routing designed to render the assessment home page that
will contain all the assessments conducted with some statistics and summary information.
'''
@assessment_bp.route('/', methods=['GET'])
def assessment_index():
    assessments = assessment_service.get_all_assessments()

    # Calculate assessment statistics
    total_assessments = len(assessments)
    completed_assessments = sum(
        1 for a in assessments if a['status'] == 'completed'
    )
    running_assessments = sum(
        1 for a in assessments if a['status'] == 'running'
    )
    pending_assessments = sum(
        1 for a in assessments if a['status'] == 'pending'
    )
    failed_assessments = sum(
        1 for a in assessments if a['status'] == 'failed'
    )

    return render_template(
        'assessments.html',
        assessments=assessments,
        total_assessments=total_assessments,
        completed_assessments=completed_assessments,
        running_assessments=running_assessments,
        pending_assessments=pending_assessments,
        failed_assessments=failed_assessments
    )



'''
A routing that will render the page for a new assessment creation.
'''
@assessment_bp.route('/assessment/new', methods=['GET'])
def assessment_new():
    return render_template('assessment_new.html')


'''
A page routing designed to render the assessment detail page for a specific assessment.
The assessment ID will be provided as part of the URL path.
Example: /assessment/123 will render the detail page for the assessment with ID 123.
'''
@assessment_bp.route('/assessment/<int:assessment_id>', methods=['GET'])
def assessment_detail(assessment_id):
    return render_template('assessment_detail.html', assessment_id=assessment_id)



# ==========================================
# API Routes
# ==========================================

'''
Route for retrieving all assessments stored in the database
The routing information will be passed as arguments in the query parameters that are part of the URL.
Example: /get-assessments?target_id=123 will return the assessments for the target with ID 123.
If no target id is provided, all assessments will be returned.
'''
@assessment_bp.route('/api/get-assessments', methods=['GET'])
def get_assessments():
    target_id = request.args.get("target_id", type=int)
    assessments = assessment_service.get_all_assessments(target_id)
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


'''
A route for updating an existing assessment.
The assessment ID will be provided as part of the URL path, and the updated assessment data will be provided in the request body as JSON.
Example: /api/assessments/123 will update the assessment with ID 123.
'''
@assessment_bp.route('/api/assessments/<int:assessment_id>', methods=['PUT'])
def update_assessment(assessment_id):
    data = request.get_json()
    assessment = assessment_service.update_assessment(assessment_id, data)
    return jsonify(assessment)