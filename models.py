# secure-coding/models.py
from datetime import datetime
from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(80), unique=True, nullable=False)
    pw_hash   = db.Column(db.String(128), nullable=False)
    balance   = db.Column(db.Integer, default=0)
    is_admin  = db.Column(db.Boolean, default=False)
    blocked   = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    seller_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name        = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price       = db.Column(db.Integer, nullable=False)
    blocked     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    sent_at     = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    from_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount     = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
