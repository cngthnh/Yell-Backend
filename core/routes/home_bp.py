from ..controllers.home_controller import *

from flask import Blueprint

task_bp = Blueprint('task_bp', __name__)
task_bp.route('/', methods=['GET'])(homepage)