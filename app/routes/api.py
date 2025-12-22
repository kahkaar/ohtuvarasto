"""REST API routes."""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from marshmallow import ValidationError

from app.services import WarehouseService, ItemService, AuditService
from app.schemas import (
    warehouse_schema,
    item_schema,
    items_schema,
    transfer_schema,
    audit_logs_schema,
)

api_bp = Blueprint("api", __name__)


def api_error(message, status_code=400):
    """Return a JSON error response."""
    return jsonify({"error": message}), status_code


def require_edit_permission(func):
    """Decorator to require edit permission."""
    from functools import wraps

    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return api_error("Authentication required", 401)
        if not current_user.can_edit():
            return api_error("Permission denied", 403)
        return func(*args, **kwargs)

    return decorated


def require_delete_permission(func):
    """Decorator to require delete permission."""
    from functools import wraps

    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return api_error("Authentication required", 401)
        if not current_user.can_delete():
            return api_error("Permission denied", 403)
        return func(*args, **kwargs)

    return decorated

@api_bp.route("/warehouses", methods=["GET"])
@login_required
def list_warehouses():
    """List all warehouses."""
    search = request.args.get("search")
    warehouse_data = WarehouseService.get_all_with_totals(search=search)
    result = []
    for data in warehouse_data:
        w_data = warehouse_schema.dump(data["warehouse"])
        w_data["total_quantity"] = data["total_quantity"]
        result.append(w_data)
    return jsonify(result)


@api_bp.route("/warehouses", methods=["POST"])
@require_edit_permission
def create_warehouse():
    """Create a new warehouse."""
    try:
        data = warehouse_schema.load(request.json)
    except ValidationError as err:
        return api_error(err.messages, 400)

    # Check if code exists
    if WarehouseService.get_by_code(data["code"]):
        return api_error("Warehouse code already exists", 409)

    warehouse = WarehouseService.create(data, user=current_user)
    return jsonify(warehouse_schema.dump(warehouse)), 201


@api_bp.route("/warehouses/<int:warehouse_id>", methods=["GET"])
@login_required
def get_warehouse(warehouse_id):
    """Get a specific warehouse."""
    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        return api_error("Warehouse not found", 404)

    data = warehouse_schema.dump(warehouse)
    data["total_quantity"] = warehouse.get_total_quantity()
    return jsonify(data)


@api_bp.route("/warehouses/<int:warehouse_id>", methods=["PUT"])
@require_edit_permission
def update_warehouse(warehouse_id):
    """Update a warehouse."""
    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        return api_error("Warehouse not found", 404)

    try:
        data = warehouse_schema.load(request.json, partial=True)
    except ValidationError as err:
        return api_error(err.messages, 400)

    # Check if code is taken by another warehouse
    if "code" in data:
        existing = WarehouseService.get_by_code(data["code"])
        if existing and existing.id != warehouse.id:
            return api_error("Warehouse code already exists", 409)

    warehouse = WarehouseService.update(warehouse, data, user=current_user)
    return jsonify(warehouse_schema.dump(warehouse))


@api_bp.route("/warehouses/<int:warehouse_id>", methods=["DELETE"])
@require_delete_permission
def delete_warehouse(warehouse_id):
    """Delete a warehouse."""
    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        return api_error("Warehouse not found", 404)

    try:
        WarehouseService.delete(warehouse, user=current_user)
    except ValueError as e:
        return api_error(str(e), 400)

    return "", 204


# Item endpoints
@api_bp.route("/warehouses/<int:warehouse_id>/items", methods=["GET"])
@login_required
def list_warehouse_items(warehouse_id):
    """List items in a warehouse."""
    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        return api_error("Warehouse not found", 404)

    search = request.args.get("search")
    items = ItemService.get_all(warehouse_id=warehouse_id, search=search)
    return jsonify(items_schema.dump(items))


@api_bp.route("/warehouses/<int:warehouse_id>/items", methods=["POST"])
@require_edit_permission
def create_item(warehouse_id):
    """Add an item to a warehouse."""
    warehouse = WarehouseService.get_by_id(warehouse_id)
    if not warehouse:
        return api_error("Warehouse not found", 404)

    try:
        data = item_schema.load(request.json)
    except ValidationError as err:
        return api_error(err.messages, 400)

    data["warehouse_id"] = warehouse_id
    try:
        item = ItemService.create(data, user=current_user)
    except Exception as e:
        return api_error(str(e), 400)

    return jsonify(item_schema.dump(item)), 201


@api_bp.route("/warehouses/<int:warehouse_id>/items/<int:item_id>", methods=["GET"])
@login_required
def get_item(warehouse_id, item_id):
    """Get a specific item."""
    item = ItemService.get_by_id(item_id)
    if not item or item.warehouse_id != warehouse_id:
        return api_error("Item not found", 404)

    return jsonify(item_schema.dump(item))


@api_bp.route("/warehouses/<int:warehouse_id>/items/<int:item_id>", methods=["PUT"])
@require_edit_permission
def update_item(warehouse_id, item_id):
    """Update an item."""
    item = ItemService.get_by_id(item_id)
    if not item or item.warehouse_id != warehouse_id:
        return api_error("Item not found", 404)

    try:
        data = item_schema.load(request.json, partial=True)
    except ValidationError as err:
        return api_error(err.messages, 400)

    # Don't allow changing warehouse_id through update
    data.pop("warehouse_id", None)

    item = ItemService.update(item, data, user=current_user)
    return jsonify(item_schema.dump(item))


@api_bp.route("/warehouses/<int:warehouse_id>/items/<int:item_id>", methods=["DELETE"])
@require_delete_permission
def delete_item(warehouse_id, item_id):
    """Delete an item."""
    item = ItemService.get_by_id(item_id)
    if not item or item.warehouse_id != warehouse_id:
        return api_error("Item not found", 404)

    ItemService.delete(item, user=current_user)
    return "", 204


# Transfer endpoint
@api_bp.route("/transfers", methods=["POST"])
@require_edit_permission
def transfer_items():
    """Transfer items between warehouses."""
    try:
        data = transfer_schema.load(request.json)
    except ValidationError as err:
        return api_error(err.messages, 400)

    # Validate warehouses exist
    source = WarehouseService.get_by_id(data["source_warehouse_id"])
    destination = WarehouseService.get_by_id(data["destination_warehouse_id"])

    if not source:
        return api_error("Source warehouse not found", 404)
    if not destination:
        return api_error("Destination warehouse not found", 404)

    try:
        result = ItemService.transfer(
            source_warehouse_id=data["source_warehouse_id"],
            destination_warehouse_id=data["destination_warehouse_id"],
            item_id=data["item_id"],
            quantity=data["quantity"],
            user=current_user,
            notes=data.get("notes"),
        )
    except ValueError as e:
        return api_error(str(e), 400)

    return jsonify(
        {
            "message": "Transfer successful",
            "source_item": item_schema.dump(result["source_item"]),
            "destination_item": item_schema.dump(result["destination_item"]),
        }
    )


# Audit log endpoint
@api_bp.route("/audit", methods=["GET"])
@login_required
def list_audit_logs():
    """List audit logs with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)

    filters = {}
    if request.args.get("type"):
        filters["type"] = request.args.get("type")
    if request.args.get("user_id"):
        filters["user_id"] = request.args.get("user_id", type=int)
    if request.args.get("warehouse_id"):
        filters["warehouse_id"] = request.args.get("warehouse_id", type=int)

    pagination = AuditService.get_logs(
        page=page, per_page=per_page, filters=filters if filters else None
    )

    return jsonify(
        {
            "items": audit_logs_schema.dump(pagination.items),
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }
    )


# Items search endpoint
@api_bp.route("/items", methods=["GET"])
@login_required
def search_all_items():
    """Search items across all warehouses."""
    search = request.args.get("search")
    items = ItemService.get_all(search=search)
    return jsonify(items_schema.dump(items))
