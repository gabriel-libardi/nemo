from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from getpass import getpass
from app import User


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


with app.app_context():
    # Create a new user
    email = input("Enter your Username: ")
    password = getpass(prompt="Enter your Password: ")

    new_user = User(email, password)

    db.session.add(new_user)
    db.session.commit()

print("User added successfully.")

