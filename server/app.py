#!/usr/bin/env python3

# Standard library imports

# Remote library imports
import base64
from datetime import datetime
from flask import request,make_response,jsonify,send_from_directory
import requests.auth
import requests
from flask_restful import Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import requests
from requests.auth import HTTPBasicAuth

# Local imports
from config import app, db, api, bcrypt
# Add your model imports
from models import User, GasCylinder, Order

# Views go here!

@app.route('/')
def index():
    return '<h1>Project Server</h1>'

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    new_user = User(
        name=data['name'],
        email=data['email'], 
        password=hashed_password,
    )
    db.session.add(new_user)
    db.session.commit()
    return make_response(jsonify({'message': 'User created successfully'}), 201)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        user = User.query.filter_by(email=data['email']).first()
        if user and bcrypt.check_password_hash(user.password, data['password']):
            access_token = create_access_token(identity={'id': user.id, 'role': user.role})
            return make_response(jsonify(access_token=access_token, user=user.to_dict()), 200)
        else:
            return make_response(jsonify({'message': 'In    "name": "John Doe",valid email or password'}), 401)
    except Exception as e:
        return make_response(jsonify({'message': f'Error logging in: {str(e)}'}), 500)

@app.route('/cylinders')   
@jwt_required()
def get_cylinders():
    cylinders = GasCylinder.query.all()
    return jsonify([cylinder.to_dict() for cylinder in cylinders]), 200

       
@app.route('/cylinders', methods=['POST'])
@jwt_required()
def add_gas_cylinder():
    if 'image' not in request.files:
        return jsonify({'message': 'No image file part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    if not (request.form.get('description') and request.form.get('cylinder_type')):
        return jsonify({'message': 'Missing required fields'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    file.save(file_path)

    data = request.form
    new_gas_cylinder = GasCylinder(
        cylinder_type=data.get('cylinder_type'),
        description=data.get('description'),
        size=data.get('size'),
        buying_price=data.get('buying_price'),
        refilling_price=data.get('refilling_price'),
        image=f"/uploads/{filename}"  
    )
    db.session.add(new_gas_cylinder)
    db.session.commit()

    return jsonify({'message': 'Gas Cylinder added successfully'}), 201

@app.route('/cylinders/<int:id>', methods=['PUT'])
@jwt_required()
def update_gas_cylinder(id):
    data = request.get_json()
    gas_cylinder = GasCylinder.query.get(id)
    if gas_cylinder:
        gas_cylinder.cylinder_type= data.get('cylinder_type', gas_cylinder.cylinder_type)
        gas_cylinder.description= data.get('description', gas_cylinder.description)
        gas_cylinder.size= data.get('size', gas_cylinder.size)
        gas_cylinder.image= data.get('image', gas_cylinder.image)
        gas_cylinder.buying_price= data.get('buying_price', gas_cylinder.buying_price)
        gas_cylinder.refilling_price= data.get('refilling_price', gas_cylinder.refilling_price)

        db.session.commit()
        return jsonify({"message":"Gas Cylinder updated successfully"})
    return jsonify({"message": "Gas Cylinder not found!"})




@app.route('/cylinders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_gas_cylinder(id):
    gas_cylinder = GasCylinder.query.get(id)
    if gas_cylinder:
        db.session.delete(gas_cylinder)
        db.session.commit()
        return jsonify({"message":"Gas Cylinder deleted successfully"}), 200
    return jsonify({"message":"Gas Cylinder not found!"}), 404

@app.route('/cylinders/<int:id>/buy', methods=['POST'])
@jwt_required()
def buy_gas_cylinder(id):
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    if not user:
        return jsonify({"message": "User not found!"}), 404
    gas_cylinder = GasCylinder.query.get(id)

    if not gas_cylinder:
        return jsonify({"message": "Gas Cylinder not found"}), 404
    
    # Create Order record
    order = Order(user_id=user.id, gas_cylinder_id=gas_cylinder.id, price_paid=gas_cylinder.buying_price,order_type="BUY")
    db.session.add(order)
    
    #other logicals

    db.session.commit()
    return jsonify({"message": "You have successfully purchased this cylinder! "})



@app.route('/cylinders/<int:id>/refill', methods=['POST'])
@jwt_required()
def refill_gas_cylinder(id):
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    if not user:
        return jsonify({"message": "User not found!"}), 404
    gas_cylinder = GasCylinder.query.get(id)

    if not gas_cylinder:
        return jsonify({"message": "Gas Cylinder not found"}), 404
    
    # Create Order record
    order = Order(user_id=user.id, gas_cylinder_id=gas_cylinder.id, price_paid=gas_cylinder.buying_price,order_type="REFILL")
    db.session.add(order)
    
    #other logicals

    db.session.commit()
    return jsonify({"message": "REFILL successful!! "})



if __name__ == '__main__':
    app.run(port=5555, debug=True)

