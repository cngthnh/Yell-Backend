from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import cipher
import os
from functools import wraps
import secrets


app = Flask(__name__)

from database import getDbUri

# init SQL database connect
app.config['SQLALCHEMY_DATABASE_URI'] = getDbUri()
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.Text)
    name = db.Column(db.UnicodeText)
    hash = db.Column(db.String(32))
    def __init__(self, id, email, name, hash):
        self.id = id
        self.email = email
        self.name = name
        self.hash = hash

# load keys for signing and encrypting tokens
cipher.loadKeys()



def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):

        token = request.form.get('token')

        if token is None:
            return jsonify(message='INVALID_TOKEN'), 403

        if not cipher.accountCheck(token):
            return jsonify(message='INVALID_TOKEN'), 403

        return func(*args, **kwargs)
    return tokenCheck

@app.route('/')
def homepage():
    return 'Yell by Yellion'

@app.route('/api/auth', methods=['POST'])
def getToken():
    try:
        _tokenDict = {'username': str(request.form.get('user')), 'hash': str(request.form.get('hash'))}
        return cipher.generateToken(_tokenDict)
    except Exception:
        return jsonify(message='INVALID_CREDENTIALS'), 403

@app.route('/api/authorized', methods=['POST'])
@tokenRequired
def authorized():
    return jsonify(message='AUTHORIZED'), 200

@app.route('/api/signup', methods=['GET'])
def createAccount():
    user = User('cngthnh', '19120374@gmail.com', 'Vu Cong Thanh', 'thisisahashstring')
    db.session.add(user)
    db.session.commit()
    
if __name__ == '__main__':
    db.create_all()
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))