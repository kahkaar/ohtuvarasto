"""Authentication routes."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from app import db
from app.models import User, Role

auth_bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    """Form for user login."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")


class RegisterForm(FlaskForm):
    """Form for user registration."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
    )


class CreateUserForm(FlaskForm):
    """Form for admin user creation."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6)]
    )
    role = SelectField(
        "Role",
        choices=[
            (Role.VIEWER.value, "Viewer"),
            (Role.MANAGER.value, "Manager"),
            (Role.ADMIN.value, "Admin"),
        ],
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("main.dashboard"))
        flash("Invalid username or password", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "error")
            return render_template("auth/register.html", form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered", "error")
            return render_template("auth/register.html", form=form)

        user = User(
            username=form.username.data, email=form.email.data, role=Role.VIEWER.value
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/users")
@login_required
def users():
    """List all users (admin only)."""
    if not current_user.has_role(Role.ADMIN):
        flash("Access denied", "error")
        return redirect(url_for("main.dashboard"))

    all_users = User.query.order_by(User.username).all()
    return render_template("auth/users.html", users=all_users)


@auth_bp.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    """Create a new user (admin only)."""
    if not current_user.has_role(Role.ADMIN):
        flash("Access denied", "error")
        return redirect(url_for("main.dashboard"))

    form = CreateUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "error")
            return render_template("auth/create_user.html", form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered", "error")
            return render_template("auth/create_user.html", form=form)

        user = User(
            username=form.username.data, email=form.email.data, role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash(f"User {user.username} created successfully!", "success")
        return redirect(url_for("auth.users"))

    return render_template("auth/create_user.html", form=form)


@auth_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    """Delete a user (admin only)."""
    if not current_user.has_role(Role.ADMIN):
        flash("Access denied", "error")
        return redirect(url_for("main.dashboard"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.users"))

    if user.id == current_user.id:
        flash("Cannot delete your own account", "error")
        return redirect(url_for("auth.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted", "success")
    return redirect(url_for("auth.users"))
