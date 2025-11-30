"""Main routes for the application."""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.services import WarehouseService, ItemService

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page - redirect to dashboard or login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard showing warehouse overview."""
    warehouses = WarehouseService.get_all()

    # Get low stock items (quantity <= 10)
    low_stock_items = ItemService.get_all(filters={"low_stock": 10})

    return render_template(
        "dashboard.html",
        warehouses=warehouses,
        low_stock_items=low_stock_items,
    )
