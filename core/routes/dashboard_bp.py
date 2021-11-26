from ..controllers.dashboard_controller import *

from flask import Blueprint

dashboard_bp = Blueprint('dashboard_bp', __name__)
dashboard_bp.route('', methods=['GET'])(getDashboard)
dashboard_bp.route('', methods=['POST'])(createDashboard)
dashboard_bp.route('', methods=['PATCH'])(updateDashboard)
dashboard_bp.route('', methods=['DELETE'])(deleteDashboard)
dashboard_bp.route('/permission', methods=['POST'])(grantDashboardPermission)
dashboard_bp.route('/permission', methods=['DELETE'])(removeDashboardPermission)
dashboard_bp.route('/invitation', methods=['GET'])(confirmDashboardInvitation)