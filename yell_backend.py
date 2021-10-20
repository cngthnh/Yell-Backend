from sqlalchemy.exc import InvalidRequestError
from core.routes import *

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            db.session.commit()
    except InvalidRequestError:
        db.session.rollback()
        raise Exception('cant create tables')
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))