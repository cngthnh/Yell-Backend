import os
from flask_sqlalchemy import SQLAlchemy

def getDbUri():
    db_user = 'yell-backend'
    db_pass = '8SA46Wil8iEJt|9]z'
    db_name = 'yell'
    db_host = '34.69.77.182:3306'

    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = 'learning-327601:us-central1:yell-data'

    URI = '{}://{}:{}@{}:{}/{}?charset={}&unix_sock={}/{}/.s.PGSQL.5432'.format(
            "postgresql+pg8000",
            db_user,
            db_pass,
            db_name,
            db_socket_dir,
            cloud_sql_connection_name,
            'utf8')
    return URI
