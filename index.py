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

def heartbeater():
    try:
        while (True):
            for _ in range(HEARTBEAT_RETRIES):
                response = requests.post(os.environ['SERVICE_DISCOVERY_URL'], 
                    data = json.dumps({"name": "Yell API Service", "url": os.environ['YELL_MAIN_URL']}), 
                    headers = {'content-type': 'application/json'})
                print(response)
                if response.ok:
                    break
            time.sleep(HEARTBEAT_INTERVAL)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    print("== START_MAIN ==")
    heartbeatWorker = threading.Thread(target=heartbeater)
    heartbeatWorker.start()
    print("== START_APP ==")
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
    print("== END_MAIN ==")