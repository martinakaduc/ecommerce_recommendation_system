from flask import Flask, Blueprint, render_template, request, jsonify, url_for, redirect, session
import requests
import json
from app.models import CategoryManagement, ItemManagement
from app.configs import NUMBER_PRODUCT_ON_HOME_PER_CAT

general_bp = Blueprint("general_bp", __name__ , template_folder="templates/general", static_url_path="/static")

@general_bp.route("/")
def home():
    root_categories = CategoryManagement.get_root_categories()
    if "username" in session:
        pass

    popular_products = {}
    for category in root_categories:
        popular_products[category.category] = ItemManagement.get_popular_products(category, NUMBER_PRODUCT_ON_HOME_PER_CAT)
    # print(popular_products)
    return render_template("index.html", title="Home", categories=root_categories, popular_products=popular_products)

@general_bp.route("/search")
def search():
    query = request.args['keyword']
    products = requests.get("http://localhost:5000/api/products/groceries/"+query)
    return render_template("search_results.html",search_results={"products":products.json(), "number":len(products.json())}, title=query)

