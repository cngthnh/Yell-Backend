from ..controllers.auth_controller import *

from flask import Blueprint

auth_bp = Blueprint('auth_bp', __name__)
auth_bp.route('/', methods=['GET'])(authorized)