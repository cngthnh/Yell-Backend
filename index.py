from core.loader import *
from core.routes.auth_bp import auth_bp
from core.routes.user_bp import user_bp
from core.routes.dashboard_bp import dashboard_bp
from core.routes.task_bp import task_bp
from core.routes.budget_bp import budget_bp
from core.routes.transaction_bp import transaction_bp
from core.routes.home_bp import home_bp
from core.routes.notif_bp import notif_bp
import threading

app.register_blueprint(auth_bp, url_prefix=AUTH_ENDPOINT)
app.register_blueprint(user_bp, url_prefix=USERS_ENDPOINT)
app.register_blueprint(dashboard_bp, url_prefix=DASHBOARDS_ENDPOINT)
app.register_blueprint(task_bp, url_prefix=TASKS_ENDPOINT)
app.register_blueprint(budget_bp, url_prefix=BUDGETS_ENDPOINT)
app.register_blueprint(transaction_bp, url_prefix=TRANSACTIONS_ENDPOINT)
app.register_blueprint(home_bp, url_prefix=HOME_ENDPOINT)
app.register_blueprint(notif_bp, url_prefix=NOTIF_ENDPOINT)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 80))
    heartbeatWorker = threading.Thread(target=heartbeater)
    heartbeatWorker.start()