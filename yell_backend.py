from core.loader import *
import sys
from core.routes.auth_bp import auth_bp

if __name__ == '__main__':
    app.register_blueprint(auth_bp, url_prefix=AUTH_ENDPOINT)
    print(app.blueprints.keys())
    sys.stdout.flush()
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 443))