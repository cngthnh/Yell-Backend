from ..controllers.user_controller import *

from flask import Blueprint

user_bp = Blueprint('user_bp', __name__)
user_bp.route('', methods=['GET'])(getUserProfile)
user_bp.route('', methods=['POST'])(createAccount)
user_bp.route('', methods=['PATCH'])(updateAccount)
user_bp.route('', methods=['DELETE'])(deleteAccount)
user_bp.route('/verify/<token>', methods=['GET'])(verifyAccount)
user_bp.route('/verify', methods=['POST'])(verifyAccountByCode)
user_bp.route('/verify/resend', methods=['POST'])(resendVerificationEmail)
user_bp.route('/check', methods=['GET'])(checkAccount)