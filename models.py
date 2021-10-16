from database import db

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
