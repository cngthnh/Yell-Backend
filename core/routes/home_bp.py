from ..controllers.home_controller import *

from flask import Blueprint

home_bp = Blueprint('home_bp', __name__)
home_bp.route('', methods=['GET'])(homepage)