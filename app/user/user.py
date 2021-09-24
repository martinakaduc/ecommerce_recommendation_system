from flask import Blueprint, Flask , jsonify, render_template, session, request, redirect, url_for
from app.models import UserManagement, OrderManagement, ReviewManagement
from app.auth.auth import login_required

user_bp = Blueprint("user_bp", __name__, template_folder="templates/user")

@user_bp.route("/profile", methods=["GET"])
@login_required
def main():
    userId = session['username']
    user = UserManagement.get(userId)
    return render_template("profile.html",
                            title="User Profile",
                            user=user)

@user_bp.route("/orders", methods=["GET"])
@login_required
def view_orders():
    userId = session["username"]
    orders, order_details, items = OrderManagement.get_orders(userId)
    return render_template("orders.html",
                            title="Order History",
                            orders=orders,
                            order_details=order_details,
                            items=items)

@user_bp.route("/reviews", methods=["GET"])
@login_required
def view_reviews():
    userId = session['username']

    products_reviews = ReviewManagement.get_reviews_of_user(userId)
    return render_template("reviews.html", 
                            products_reviews=products_reviews,
                            title="All Your Reviews")