from datetime import datetime
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

from config import db

# Models go here!

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(25), default='user')
    
    @validates('email')
    def validate_email(self, key, address):
        if '@' not in address:
            raise ValueError('Failed email validation')
        return address
    
    def __repr__(self):
        return f'<User {self.name}>'
    

class GasCylinder(db.Model,SerializerMixin):
    __tablename__ = 'gas_cylinders'

    id = db.Column(db.Integer,primary_key=True)
    cylinder_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100),nullable=False)
    image = db.Column(db.String(255), nullable=True)
    size = db.Column(db.String(10), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    refilling_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Cylinder {self.cylinder_type}>'
    

class Order(db.Model,SerializerMixin):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gas_cylinder_id = db.Column(db.Integer, db.ForeignKey('gas_cylinders.id'), nullable=False)
    #change purchase_date to order_date
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    order_type = db.Column(db.String(10),nullable=False)
    price_paid = db.Column(db.Float, nullable=False)
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    gas_cylinder = db.relationship('GasCylinder', backref=db.backref('orders', lazy=True))
