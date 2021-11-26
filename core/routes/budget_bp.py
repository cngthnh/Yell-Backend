from ..controllers.budget_controller import *

from flask import Blueprint

budget_bp = Blueprint('budget_bp', __name__)
budget_bp.route('/', methods=['GET'])(getBudget)
budget_bp.route('/', methods=['POST'])(createBudget)
budget_bp.route('/', methods=['PATCH'])(updateBudget)
budget_bp.route('/', methods=['DELETE'])(deleteBudget)