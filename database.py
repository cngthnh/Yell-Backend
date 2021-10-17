import os
from flask_sqlalchemy import SQLAlchemy

def getDbUri():
    db_user = 'yell-backend'
    db_pass = '8SA46Wil8iEJt|9]z'
    db_name = 'yell'
    db_host = '10.80.144.4:5432'

    host_args = db_host.split(":")
    if len(host_args) == 1:
        db_hostname = db_host
        db_port = os.environ["DB_PORT"]
    elif len(host_args) == 2:
        db_hostname, db_port = host_args[0], int(host_args[1])

    URI = '{}://{}:{}@{}:{}/{}'.format(
            "postgresql+pg8000",
            db_user,
            db_pass,
            db_hostname,
            db_port,
            db_name)
    return URI

db = SQLAlchemy()