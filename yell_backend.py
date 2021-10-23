from core.routes import *

if __name__ == '__main__':
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 443))