"""Item routes for web UI."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

from app.services import WarehouseService, ItemService

items_bp = Blueprint("items", __name__)


class ItemForm(FlaskForm):
    """Form for creating/editing items."""

    sku = StringField("SKU", validators=[DataRequired(), Length(min=1, max=50)])
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField("Description", validators=[Optional()])
    quantity = FloatField(
        "Quantity", validators=[DataRequired(), NumberRange(min=0)]
    )
    unit = StringField("Unit", validators=[Optional(), Length(max=20)])
    batch_number = StringField(
        "Batch Number", validators=[Optional(), Length(max=50)]
    )
    expiry_date = DateField("Expiry Date", validators=[Optional()])


class TransferForm(FlaskForm):
    """Form for transferring items between warehouses."""

    destination_warehouse_id = SelectField(
        "Destination Warehouse", coerce=int, validators=[DataRequired()]
    )
    quantity = FloatField(
        "Quantity", validators=[DataRequired(), NumberRange(min=0.01)]
    )
    notes = TextAreaField("Notes", validators=[Optional()])


@items_bp.route("/warehouse/<int:warehouse_id>/create", methods=["GET", "POST"])
@login_required
def create_item(warehouse_id):
    """Create a new item in a warehouse."""
    if not current_user.can_edit():
        flash("You don't have permission to add items", "error")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse_id))

    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        flash("Warehouse not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    form = ItemForm()
    if form.validate_on_submit():
        data = {
            "warehouse_id": warehouse_id,
            "sku": form.sku.data,
            "name": form.name.data,
            "description": form.description.data,
            "quantity": form.quantity.data,
            "unit": form.unit.data or "units",
            "batch_number": form.batch_number.data,
            "expiry_date": form.expiry_date.data,
        }
        try:
            item = ItemService.create(data, user=current_user)
            flash(f"Item '{item.name}' added successfully!", "success")
            return redirect(
                url_for("warehouses.view_warehouse", warehouse_id=warehouse_id)
            )
        except Exception as e:
            flash(f"Error adding item: {str(e)}", "error")

    return render_template("items/create.html", form=form, warehouse=warehouse)


@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    """Edit an item."""
    item = ItemService.get_by_id(item_id)
    if not item:
        flash("Item not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    if not current_user.can_edit():
        flash("You don't have permission to edit items", "error")
        return redirect(
            url_for("warehouses.view_warehouse", warehouse_id=item.warehouse_id)
        )

    form = ItemForm(obj=item)
    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "quantity": form.quantity.data,
            "unit": form.unit.data or "units",
            "batch_number": form.batch_number.data,
            "expiry_date": form.expiry_date.data,
        }
        ItemService.update(item, data, user=current_user)
        flash("Item updated successfully!", "success")
        return redirect(
            url_for("warehouses.view_warehouse", warehouse_id=item.warehouse_id)
        )

    return render_template("items/edit.html", form=form, item=item)


@items_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    """Delete an item."""
    item = ItemService.get_by_id(item_id)
    if not item:
        flash("Item not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    if not current_user.can_delete():
        flash("You don't have permission to delete items", "error")
        return redirect(
            url_for("warehouses.view_warehouse", warehouse_id=item.warehouse_id)
        )

    warehouse_id = item.warehouse_id
    ItemService.delete(item, user=current_user)
    flash("Item deleted successfully!", "success")
    return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse_id))


@items_bp.route("/<int:item_id>/transfer", methods=["GET", "POST"])
@login_required
def transfer_item(item_id):
    """Transfer an item to another warehouse."""
    item = ItemService.get_by_id(item_id)
    if not item:
        flash("Item not found", "error")
        return redirect(url_for("warehouses.list_warehouses"))

    if not current_user.can_edit():
        flash("You don't have permission to transfer items", "error")
        return redirect(
            url_for("warehouses.view_warehouse", warehouse_id=item.warehouse_id)
        )

    # Get available destination warehouses
    all_warehouses = WarehouseService.get_all()
    destination_choices = [
        (w.id, f"{w.name} ({w.code})")
        for w in all_warehouses
        if w.id != item.warehouse_id
    ]

    form = TransferForm()
    form.destination_warehouse_id.choices = destination_choices

    if form.validate_on_submit():
        try:
            ItemService.transfer(
                source_warehouse_id=item.warehouse_id,
                destination_warehouse_id=form.destination_warehouse_id.data,
                item_id=item.id,
                quantity=form.quantity.data,
                user=current_user,
                notes=form.notes.data,
            )
            flash(
                f"Transferred {form.quantity.data} {item.unit} of {item.name}",
                "success",
            )
            return redirect(
                url_for("warehouses.view_warehouse", warehouse_id=item.warehouse_id)
            )
        except ValueError as e:
            flash(str(e), "error")

    return render_template("items/transfer.html", form=form, item=item)


@items_bp.route("/search")
@login_required
def search_items():
    """Search items across all warehouses."""
    search = request.args.get("search", "")
    items = ItemService.get_all(search=search if search else None)
    return render_template("items/search.html", items=items, search=search)
