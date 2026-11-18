
from flask import Blueprint, render_template
from services import agents_service


agents_bp = Blueprint('agents', __name__)


@agents_bp.route('/', methods=['GET'])
def agent_index():

    agents = agents_service.get_all_agents()

    return render_template(
        'agents.html',
        agents=agents
    )