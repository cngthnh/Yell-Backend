from ..controllers.static_controller import *

from flask import Blueprint

static_bp = Blueprint('static_bp', __name__)
static_bp.route('/public/<resource_name>', methods=['GET'])(getPublicStaticResource)
static_bp.route('/f5', methods=['GET'])(refreshPublicStaticResource)
static_bp.route('/<category>/<entity>/<resource_name>', methods=['GET'])(getPrivateStaticResource)