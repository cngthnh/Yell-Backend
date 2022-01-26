from ..controllers.transaction_controller import *

from flask import Blueprint

transaction_bp = Blueprint('transaction_bp', __name__)
transaction_bp.route('', methods=['GET'])(getTransaction)
transaction_bp.route('', methods=['POST'])(createTransaction)
transaction_bp.route('', methods=['PATCH'])(updateTransaction)
transaction_bp.route('', methods=['DELETE'])(deleteTransaction)