from .database import db 
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    email = db.Column(db.String(),unique=True,nullable = False)
    password = db.Column(db.String(),nullable=False)
    name = db.Column(db.String(),nullable = False)
    address = db.Column(db.String(),nullable= False)
    pincode = db.Column(db.Integer(),nullable = False)
    type = db.Column(db.String(),default="general")

    reservations = db.relationship('Reservepkspot', back_populates='user') 
 
class Parkinglot(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    prime_location_name = db.Column(db.String(),nullable = False)
    price = db.Column(db.Integer(),nullable = False)
    address = db.Column(db.String(),nullable= False)
    pincode = db.Column(db.Integer(),nullable = False)
    max_no_of_spots = db.Column(db.Integer(),nullable = False)

    spots = db.relationship('Parkingspot', backref='lot', lazy=True, cascade="all, delete-orphan")
    
class Parkingspot(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    lot_id = db.Column(db.Integer(),db.ForeignKey("parkinglot.id"),nullable= False)
    status = db.Column(db.String(1), nullable=False, default='A')

    reservations = db.relationship('Reservepkspot', backref='spot', lazy=True, cascade='all, delete-orphan')

class Reservepkspot(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    spot_id = db.Column(db.Integer(),db.ForeignKey("parkingspot.id"),nullable=False)
    user_id = db.Column(db.Integer(),db.ForeignKey("user.id"),nullable=False)
    vehicle_no =db.Column(db.String(),nullable=False)
    parking_timestamp = db.Column(db.DateTime(), nullable=False)
    leaving_timestamp = db.Column(db.DateTime(), nullable=True)
    cost_per_time = db.Column(db.Integer(),nullable = False)    
    parking_cost = db.Column(db.Float, nullable=True)

    user = db.relationship('User', back_populates='reservations')
