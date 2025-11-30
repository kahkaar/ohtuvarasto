"""Warehouse routes for web UI."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

from app.services import WarehouseService, ItemService

warehouses_bp = Blueprint("warehouses", __name__)


class WarehouseForm(FlaskForm):
    """Form for creating/editing warehouses."""

    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=100)])
    code = StringField("Code", validators=[DataRequired(), Length(min=1, max=50)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    capacity = FloatField(
        "Capacity", validators=[Optional(), NumberRange(min=0)]
    )
    contact_person = StringField(
        "Contact Person", validators=[Optional(), Length(max=100)]
    )
    notes = TextAreaField("Notes", validators=[Optional()])


@warehouses_bp.route("/")
@login_required
def list_warehouses():
    """List all warehouses."""
    search = request.args.get("search", "")
    warehouses = WarehouseService.get_all(search=search if search else None)
    return render_template(
        "warehouses/list.html", warehouses=warehouses, search=search
    )


@warehouses_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_warehouse():
    """Create a new warehouse."""
    if not current_user.can_edit():
        flash("You don't have permission to create warehouses", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    form = WarehouseForm()
    if form.validate_on_submit():
        # Check if code already exists
        if WarehouseService.get_by_code(form.code.data):
            flash("Warehouse code already exists", "error")
            return render_template("warehouses/create.html", form=form)

        data = {
            "name": form.name.data,
            "code": form.code.data,
            "address": form.address.data,
            "capacity": form.capacity.data,
            "contact_person": form.contact_person.data,
            "notes": form.notes.data,
        }
        warehouse = WarehouseService.create(data, user=current_user)
        flash(f"Warehouse '{warehouse.name}' created successfully!", "success")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse.id))

    return render_template("warehouses/create.html", form=form)


@warehouses_bp.route("/<int:warehouse_id>")
@login_required
def view_warehouse(warehouse_id):
    """View a warehouse and its items."""
    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        flash("Warehouse not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    search = request.args.get("search", "")
    items = ItemService.get_all(
        warehouse_id=warehouse_id, search=search if search else None
    )
    return render_template(
        "warehouses/view.html", warehouse=warehouse, items=items, search=search
    )


@warehouses_bp.route("/<int:warehouse_id>/edit", methods=["GET", "POST"])
@login_required
def edit_warehouse(warehouse_id):
    """Edit a warehouse."""
    if not current_user.can_edit():
        flash("You don't have permission to edit warehouses", "error")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse_id))

    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        flash("Warehouse not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    form = WarehouseForm(obj=warehouse)
    if form.validate_on_submit():
        # Check if code is taken by another warehouse
        existing = WarehouseService.get_by_code(form.code.data)
        if existing and existing.id != warehouse.id:
            flash("Warehouse code already exists", "error")
            return render_template(
                "warehouses/edit.html", form=form, warehouse=warehouse
            )

        data = {
            "name": form.name.data,
            "code": form.code.data,
            "address": form.address.data,
            "capacity": form.capacity.data,
            "contact_person": form.contact_person.data,
            "notes": form.notes.data,
        }
        WarehouseService.update(warehouse, data, user=current_user)
        flash("Warehouse updated successfully!", "success")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse.id))

    return render_template("warehouses/edit.html", form=form, warehouse=warehouse)


@warehouses_bp.route("/<int:warehouse_id>/delete", methods=["POST"])
@login_required
def delete_warehouse(warehouse_id):
    """Delete a warehouse."""
    if not current_user.can_delete():
        flash("You don't have permission to delete warehouses", "error")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse_id))

    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        flash("Warehouse not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    try:
        WarehouseService.delete(warehouse, user=current_user)
        flash("Warehouse deleted successfully!", "success")
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse_id))

    return redirect(url_for("warehouses.list_warehouses"))
