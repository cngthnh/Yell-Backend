from core.loader import *
from core.routes.auth_bp import auth_bp
from core.routes.user_bp import user_bp

app.register_blueprint(auth_bp, url_prefix=AUTH_ENDPOINT)
app.register_blueprint(user_bp, url_prefix=USERS_ENDPOINT)

if __name__ == '__main__':
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 443))