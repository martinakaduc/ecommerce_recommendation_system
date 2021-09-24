from flask import Flask, Blueprint, session, render_template, jsonify, request, abort ,redirect, url_for
from app.models import ItemManagement, CategoryManagement, Recommendation, ReviewManagement, OrderManagement
from app.configs import NUMBER_PRODUCT_PER_PAGE, NUMBER_PRODUCT_RECOMMEND, NUMBER_PRODUCT_PER_RECOMMEND
from app.auth.auth import login_required
from datetime import date
import re

products_bp = Blueprint("products_bp", __name__, template_folder="templates/products")

@products_bp.route("/", methods=["GET"])
def main():
	category = request.args.get('category', default = -1, type = int)
	page = request.args.get('page', default = 1, type = int)

	if category >= 0:
		products = ItemManagement.get_products_by_category(category, (page-1)*NUMBER_PRODUCT_PER_PAGE, NUMBER_PRODUCT_PER_PAGE)
		num_pages = ItemManagement.get_number_items(category) // NUMBER_PRODUCT_PER_PAGE + 1
		title = CategoryManagement.get_category_by_id(category)

		if title == None:
			abort(404)
		title = title.category
	
	else:
		products = ItemManagement.get_all_items((page-1)*NUMBER_PRODUCT_PER_PAGE, NUMBER_PRODUCT_PER_PAGE)
		num_pages = ItemManagement.get_number_items(category) // NUMBER_PRODUCT_PER_PAGE + 1
		title = "All Categories"

	return render_template("list.html", 
		products = products,
		title = title,
		category=category,
		current_page=page,
		num_pages=num_pages,
		product_per_page=NUMBER_PRODUCT_PER_PAGE)

@products_bp.route("/search", methods=["GET"])
def search_product():
	keyword = request.args.get('keyword', default = "", type = str)
	keyword = re.sub('[^A-Za-z0-9., ]+', '', keyword)
	page = request.args.get('page', default = 1, type = int)
	products = ItemManagement.get_item_by_keyword(keyword, (page-1)*NUMBER_PRODUCT_PER_PAGE, NUMBER_PRODUCT_PER_PAGE)
	num_pages = ItemManagement.count_item_by_keyword(keyword)

	return render_template("search.html", 
		products = products,
		title = "Search Results",
		keyword=keyword,
		current_page=page,
		num_pages=num_pages,
		product_per_page=NUMBER_PRODUCT_PER_PAGE)

@products_bp.route("/<item_id>", methods=["GET"])
def view_product(item_id):
	product = ItemManagement.get_item_by_id(item_id)
	
	if product == None:
		abort(404)
	else:
		if "username" in session:
			review_access = OrderManagement.is_bought(session["username"], item_id)
		else:
			review_access = False

		user_reviews = ReviewManagement.get_reviews_of_item(item_id)
		return render_template("view.html", 
								product=product,
								review_access=review_access,
								user_reviews=user_reviews,
								title=product.title)

@products_bp.route("/<itemId>/review", methods=["POST"])
@login_required
def write_review(itemId):
	userId = session["username"]
	overall = float(request.form["rating"])
	reviewText = request.form['reviewText']
	reviewTime = date.today().strftime("%b %d, %Y")

	result = ReviewManagement.create_review(userId, itemId, overall, reviewText, reviewTime)
	return {"result": result}

@products_bp.route("/recommendation", methods=["GET"])
@login_required
def view_recommendation():
	userId = session["username"]
	rtype = request.args.get('rtype', default = None, type = str)

	if rtype == None:
		recommend_products = {}
		recommend_products["Similar products"] = Recommendation.content_based(userId, limit=NUMBER_PRODUCT_RECOMMEND)
		recommend_products["Others also buy"] = Recommendation.collaborative_order_normal(userId, limit=NUMBER_PRODUCT_RECOMMEND)
		recommend_products["Others also review"] = Recommendation.collaborative_review_normal(userId, limit=NUMBER_PRODUCT_RECOMMEND)
		recommend_products["Products you'd love"] = Recommendation.collaborative_review_ml(userId, limit=NUMBER_PRODUCT_RECOMMEND)

		return render_template("general_recommend.html", 
							recommend_products=recommend_products,
							title="Your Recommendation")

	elif rtype == "similar_products":
		recommend_products = Recommendation.content_based(userId, limit=NUMBER_PRODUCT_PER_RECOMMEND)
		
		return render_template("list_recommend.html", 
							products=recommend_products,
							title="Similar Products")

	elif rtype == "others_also_buy":
		recommend_products = Recommendation.collaborative_order_normal(userId, limit=NUMBER_PRODUCT_PER_RECOMMEND)
		
		return render_template("list_recommend.html", 
							products=recommend_products,
							title="Others Also Buy")

	elif rtype == "others_also_review":
		recommend_products = Recommendation.collaborative_review_normal(userId, limit=NUMBER_PRODUCT_PER_RECOMMEND)
		
		return render_template("list_recommend.html", 
							products=recommend_products,
							title="Others Also Review")

	elif rtype == "products_you'd_love":
		recommend_products = Recommendation.collaborative_review_ml(userId, limit=NUMBER_PRODUCT_PER_RECOMMEND)
		
		return render_template("list_recommend.html", 
							products=recommend_products,
							title="Products You'd Love")