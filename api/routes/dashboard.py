from flask import Blueprint, render_template
from services import dashboard_service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
def dashboard_index():
    assessments = dashboard_service.get_all_assessments()

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
        'dashboard.html',
        assessments=assessments,
        total_assessments=total_assessments,
        completed_assessments=completed_assessments,
        running_assessments=running_assessments,
        pending_assessments=pending_assessments,
        failed_assessments=failed_assessments
    )