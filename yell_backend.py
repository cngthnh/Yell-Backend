from flask import Flask, request, jsonify
import cipher
import os
from functools import wraps
import database

app = Flask(__name__)

# load keys for signing and encrypting tokens
cipher.getEncKey()
cipher.getSigKey()

# init SQL database connect
engine = database.init()
engine.connect()

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
    
if __name__ == '__main__':
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))