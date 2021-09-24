from flask import Blueprint, render_template, session, request
from app.models import CartManagement
from app.auth.auth import login_required
from datetime import date

cart_bp = Blueprint("cart_bp", __name__, template_folder = "templates")

@cart_bp.route("/view", methods=["GET"])
@login_required
def main():
	userId = session["username"]
	orders, products = CartManagement.get_items_of_user(userId)
	return render_template("cart/view.html", title="Cart", orders=orders, products=products)

@cart_bp.route("/add", methods=["POST"])
@login_required
def addCart():
	itemId = request.form["itemId"]
	quantity = int(request.form["quantity"])
	userId = session["username"]

	result = CartManagement.add_to_cart(userId, itemId, quantity)
	return {"result": result}

@cart_bp.route("/remove", methods=["POST"])
@login_required
def removeCart():
	pass

@cart_bp.route("/count", methods=["POST"])
@login_required
def countItems():
	userId = session["username"]
	count = CartManagement.count_items(userId)
	return {"item_count": count}

@cart_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
	userId = session["username"]
	time = date.today().strftime("%b %d, %Y")
	result = CartManagement.checkout(userId, time)
	return {"result": result}

@cart_bp.route("/update", methods=["POST"])
@login_required
def update():
	userId = session["username"]
	result = CartManagement.update_whole_cart(userId, dict(request.form))
	return {"result": result}