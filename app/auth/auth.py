from flask import Blueprint, Flask , jsonify, render_template, session, request, redirect, url_for
from app.models import UserManagement
import hashlib
from .forms import RegistrationForm, LoginForm
from functools import wraps

auth_bp = Blueprint("auth_bp", __name__, template_folder="templates/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def main():
	success = True
	if request.method == "POST":
		form = LoginForm()

		username = request.form['username']
		password = request.form['password']
		password = hashlib.sha256(str(password).encode()).hexdigest()
		result = UserManagement.verify(username, password)

		if result != None:
			session['username'] = username
			session['name'] = result.name
			return redirect(url_for("general_bp.home"))
		else:
			success = False

	return render_template("login.html", title="Login", success=success)

@auth_bp.route("/register", methods=["GET","POST"])
def signup():
	success = True
	if request.method == "POST":
		form = RegistrationForm()

		fname = request.form['fname']
		lname = request.form['lname']
		name = fname + " " + lname

		username = request.form['username']
		password = request.form['password']
		confirm_password = request.form['confirm_password']
		password = hashlib.sha256(str(password).encode()).hexdigest()
		confirm_password = hashlib.sha256(str(confirm_password).encode()).hexdigest()

		if confirm_password == password and UserManagement.add(username, name, password) != None:
			return redirect(url_for("auth_bp.main"))
		else:
			success = False

	return render_template("signup.html", title ="register", success=success)

@auth_bp.route("/logout", methods=["GET"])
def logout():
	if request.method == "GET":
		if "username" not in session:
			return redirect(url_for("general_bp.home"))

		del session['username']
		del session['name']

		return redirect(url_for("general_bp.home"))

@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_pass():
	return render_template("forgot_password.html", title="forgot password")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for("auth_bp.main", next=request.url))
        return f(*args, **kwargs)
    return decorated_function