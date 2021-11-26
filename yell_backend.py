from core.loader import *
from core.routes.auth_bp import auth_bp

if __name__ == '__main__':
    app.register_blueprint(auth_bp, url_prefix=AUTH_ENDPOINT)
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 443))