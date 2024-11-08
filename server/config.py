# Standard library imports

# Remote library imports
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# Local imports

# Instantiate app, set attributes
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong random string
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.json.compact = False

# M-Pesa configuration
app.config['MPESA_CONSUMER_KEY'] = 'b6Yww7PSARWgQihM21XrVDz8XpGKT5FMIJ0QdAvaiTffEmF0'
app.config['MPESA_CONSUMER_SECRET'] = 'xYCeNLWGvIh7izjtG5RshBJfeS8x4BA1QodWGcv3MBCuRGR0OVXHOUNAwWZfclVM'
app.config['MPESA_BUSINESS_SHORT_CODE'] = '174379'  
app.config['MPESA_PASS_KEY'] = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'  
app.config['MPESA_TRANSACTION_TYPE'] = 'CustomerPayBillOnline'
app.config['MPESA_CALLBACK_URL'] = 'https://734a-80-240-201-168.ngrok-free.app/mpesa-callback'

# Define metadata, instantiate db
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate(app, db)
db.init_app(app)

# Instantiate REST API
api = Api(app)

# Instantiate CORS
CORS(app)
