from sqlalchemy.exc import InvalidRequestError
from utils.routes import *

if __name__ == '__main__':
    db.create_all()
    try:
        db.session.commit()
    except InvalidRequestError:
        db.session.rollback()
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))