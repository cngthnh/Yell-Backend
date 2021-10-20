from sqlalchemy.exc import InvalidRequestError
from core.routes import *

if __name__ == '__main__':
    try:
        db.create_all()
        db.session.commit()
    except Exception:
        db.session.rollback()
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))