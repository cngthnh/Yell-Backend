from ..controllers.task_controller import *

from flask import Blueprint

task_bp = Blueprint('task_bp', __name__)
task_bp.route('/', methods=['GET'])(getTask)
task_bp.route('/', methods=['POST'])(createTask)
task_bp.route('/', methods=['PATCH'])(updateTask)
task_bp.route('/', methods=['DELETE'])(deleteTask)