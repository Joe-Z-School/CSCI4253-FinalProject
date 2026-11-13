# Routes for managing targets

from flask import Blueprint, request, jsonify, render_template
from services import targets_service


targets_bp = Blueprint('targets', __name__)


@targets_bp.route('/targets', methods=['GET'])
def get_targets():
    enabled_only = request.args.get('enabled_only', 'true').lower() == 'true'
    targets = targets_service.get_all_targets(enabled_only=enabled_only)
    return jsonify(targets)