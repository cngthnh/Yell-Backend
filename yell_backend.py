from core.loader import *
import sys
from core.routes.auth_bp import auth_bp

app.register_blueprint(auth_bp, url_prefix=AUTH_ENDPOINT)
print("BLUEPRINTS HERE")
sys.stdout.flush()
raise Exception(app.blueprints.keys())

if __name__ == '__main__':
    print('MAINNN')
    
    #app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 443))