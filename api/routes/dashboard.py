
from flask import Blueprint, render_template
from services import dashboard_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
def dashboard_index():

    summary = dashboard_service.get_assessment_summary()

    counts = dashboard_service.get_dashboard_counts()

    recent_assessments = dashboard_service.get_all_assessments(
        limit=5
    )

    agents = dashboard_service.get_agent_overview()

    return render_template(
        'dashboard.html',

        # Assessment statistics
        **summary,

        # Target and agent statistics
        **counts,

        # Dashboard information
        recent_assessments=recent_assessments,
        agents=agents
    )
