from ..controllers.notif_controller import *

from flask import Blueprint

notif_bp = Blueprint('notif_bp', __name__)
notif_bp.route('', methods=['GET'])(getNotifications)
notif_bp.route('/confirm', methods=['POST'])(confirmNotification)
notif_bp.route('/read', methods=['PATCH'])(markAsRead)
notif_bp.route('/unread', methods=['PATCH'])(markAsUnread)