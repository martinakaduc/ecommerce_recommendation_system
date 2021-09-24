from flask import Flask, g, abort , session, redirect, url_for, request
from app.general.general import general_bp
from app.products.products import  products_bp
from app.auth.auth import auth_bp	
from app.cart.cart import cart_bp
from app.user.user import user_bp
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
from app.utils import env
from neomodel import config
import os

load_dotenv(find_dotenv())
config.DATABASE_URL = os.environ["NEO4J_BOLT_URL"]
# print("Neo4J: ", os.environ["NEO4J_BOLT_URL"])

app = Flask(__name__)
cors = CORS(app)
app.secret_key = env('SECRET_KEY')

@app.before_request
def run():
	if 'username' in session:
		redirect("/")
	else:
		redirect("/auth/login")
		
app.register_blueprint(general_bp)
app.register_blueprint(products_bp, url_prefix="/products")
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(cart_bp, url_prefix="/cart")
