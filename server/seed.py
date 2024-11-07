#!/usr/bin/env python3

# Standard library imports
from random import randint, choice as rc

# Remote library imports
from faker import Faker

# Local imports
from app import app
from models import db, User, GasCylinder  # Import the models

if __name__ == '__main__':
    fake = Faker()
    with app.app_context():
        print("Starting seed...")

        # Clear existing data
        User.query.delete()
        GasCylinder.query.delete()
        db.session.commit()

        # Seed Users
        users = []
        for _ in range(5):  # Adjust the number as needed
            user = User(
                name=fake.name(),
                email=fake.unique.email(),
                password=fake.password(),
                role=rc(['user', 'admin'])  # Randomly choose a role
            )
            if user.role == 'admin':
                print(f"Username:{user.name}, password:{user.password}")
            users.append(user)
            db.session.add(user)

        # Define shared attributes for each cylinder type
        cylinder_attributes = {
            "Total": {
                "description": "Standard TOTAL gas cylinder",
                "image": "https://example.com/type_a_image.jpg",
                "buying_price": 150.00,
                "refilling_price": 50.00
            },
            "Pro Gas": {
                "description": "Standard PRO gas cylinder",
                "image": "https://example.com/type_b_image.jpg",
                "buying_price": 200.00,
                "refilling_price": 60.00
            },
            "Hashi": {
                "description": "Standard HASHI gas cylinder",
                "image": "https://example.com/type_c_image.jpg",
                "buying_price": 250.00,
                "refilling_price": 70.00
            },
            "Sea Gas": {
                "description": "Standard SEA gas cylinder",
                "image": "https://example.com/type_c_image.jpg",
                "buying_price": 250.00,
                "refilling_price": 70.00
            }
        }

        # Seed Gas Cylinders
        gas_cylinders = []
        for _ in range(18):  # Adjust the number as needed
            cylinder_type = rc(list(cylinder_attributes.keys()))

            # Retrieve the attributes for the selected type
            attributes = cylinder_attributes[cylinder_type]
            
            gas_cylinder = GasCylinder(
                cylinder_type=cylinder_type,
                description=attributes["description"],
                image=attributes["image"],
                size=rc(['Small','Large']),
                buying_price=attributes["buying_price"],
                refilling_price=attributes["refilling_price"]
            )
            
            gas_cylinders.append(gas_cylinder)
            db.session.add(gas_cylinder)

        # Commit all data to the database
        db.session.commit()
        print("Seed complete!")
