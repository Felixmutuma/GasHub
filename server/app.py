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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


#Mpesa payment helper functions
def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=HTTPBasicAuth(app.config['MPESA_CONSUMER_KEY'], app.config['MPESA_CONSUMER_SECRET']))
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return jsonify(f"Failed to get access token: {response.status_code}, {response.text}")

def get_password():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = app.config['MPESA_BUSINESS_SHORT_CODE'] + app.config['MPESA_PASS_KEY'] + timestamp
    return base64.b64encode(data_to_encode.encode()).decode('utf-8')

def format_phone_number(number):
    if number.startswith('0'):
        return f'254{number[1:]}'
    elif number.startswith('254'):
        return number
    else:
        raise ValueError("Invalid phone number format")



@app.route('/cylinders/<int:id>/buy', methods=['POST'])
@jwt_required()
def buy_gas_cylinder(id):
    data = request.get_json()
    current_user = get_jwt_identity()['id']
    user = User.query.get(current_user)
    if not user:
        return jsonify({"message": "User not found!"}), 404
    gas_cylinder = GasCylinder.query.get(id)

    if not gas_cylinder:
        return jsonify({"message": "Gas Cylinder not found"}), 404
    
    amount = gas_cylinder.buying_price
    phone_number = data.get('phone_number')
    
    try:
        formatted_phone_number = format_phone_number(phone_number)
    except ValueError:
        return jsonify({'message': 'Invalid phone number format'}), 400
    
        # Initiate M-Pesa payment
    access_token = get_access_token()
    if not access_token:
        return jsonify({'message': 'Failed to get access token for payment. Please try again.'}), 500

    password = get_password()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    payload = {
        "BusinessShortCode": app.config['MPESA_BUSINESS_SHORT_CODE'],
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": app.config['MPESA_TRANSACTION_TYPE'],
        "Amount": amount,
        "PartyA": formatted_phone_number,
        "PartyB": app.config['MPESA_BUSINESS_SHORT_CODE'],
        "PhoneNumber": formatted_phone_number,
        "CallBackURL": app.config['MPESA_CALLBACK_URL'],
        "AccountReference": f"GasHub",
        "TransactionDesc": f"Payment for Cylinder {gas_cylinder.cylinder_type}"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    #print(f"M-Pesa request payload: {payload}")

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        mpesa_response = response.json()
        #print(f"mpesa response:{mpesa_response}")

        # Create Order record
        order = Order(user_id=user.id, 
                      gas_cylinder_id=gas_cylinder.id, 
                      price_paid=amount,
                      order_type="BUY",
                      merchant_request_id=mpesa_response.get('MerchantRequestID'),
                      checkout_request_id=mpesa_response.get('CheckoutRequestID'))
        db.session.add(order)
        
        #other logicals

        db.session.commit()
        return jsonify({"message": "You have successfully purchased this cylinder! "}),200
    else:
        return jsonify({'message': 'Failed to initiate payment. Please try again.'}), 400
    

@app.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json()
        print(f"Callback data received: {data}")

        result_code = data['Body']['stkCallback']['ResultCode']
        merchant_request_id = data['Body']['stkCallback']['MerchantRequestID']

        
        order = Order.query.filter_by(merchant_request_id=merchant_request_id).first()
        if not order:
            print(f"No booking found for MerchantRequestID: {merchant_request_id}")
            return jsonify({'message': 'Booking not found'}), 404

        if result_code == 0:  # Successful payment
            mpesa_receipt_number = data['Body']['stkCallback']['CallbackMetadata']['Item'][1]['Value']
    
            order.payment_status = 'completed'
            order.mpesa_receipt_number = mpesa_receipt_number

            #update booked status

            # gas_cylinder = GasCylinder.query.get(order.space_id)
            # if gas_cylinder:
            #     gas_cylinder.booked = True

            db.session.commit()
            print(f"Payment successful for booking ID {order.id}")
        else:
            order.payment_status = 'failed'
            db.session.commit()
            print(f"Payment failed for booking ID {order.id}")

        return jsonify({'message': 'Callback processed successfully'}), 200

    except Exception as e:
        print(f"Error in mpesa_callback: {str(e)}")
        return jsonify({'message': 'Error processing callback'}), 500



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

