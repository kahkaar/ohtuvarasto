"""Marshmallow schemas for request/response validation."""

from marshmallow import Schema, fields, validate, validates, ValidationError


class UserSchema(Schema):
    """Schema for User model."""

    id = fields.Int(dump_only=True)
    username = fields.Str(
        required=True, validate=validate.Length(min=3, max=80)
    )
    email = fields.Email(required=True)
    role = fields.Str(
        validate=validate.OneOf(["admin", "manager", "viewer"]), load_default="viewer"
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class WarehouseSchema(Schema):
    """Schema for Warehouse model."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    address = fields.Str(validate=validate.Length(max=255), allow_none=True)
    capacity = fields.Float(allow_none=True)
    contact_person = fields.Str(validate=validate.Length(max=100), allow_none=True)
    notes = fields.Str(allow_none=True)
    metadata_json = fields.Dict(load_default=dict)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    total_quantity = fields.Float(dump_only=True)

    @validates("capacity")
    def validate_capacity(self, value):
        """Validate capacity is non-negative."""
        if value is not None and value < 0:
            raise ValidationError("Capacity must be non-negative.")


class ItemSchema(Schema):
    """Schema for Item model."""

    id = fields.Int(dump_only=True)
    warehouse_id = fields.Int(required=True)
    sku = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    quantity = fields.Float(required=True)
    unit = fields.Str(validate=validate.Length(max=20), load_default="units")
    batch_number = fields.Str(validate=validate.Length(max=50), allow_none=True)
    expiry_date = fields.Date(allow_none=True)
    metadata_json = fields.Dict(load_default=dict)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates("quantity")
    def validate_quantity(self, value):
        """Validate quantity is non-negative."""
        if value < 0:
            raise ValidationError("Quantity must be non-negative.")


class TransferSchema(Schema):
    """Schema for item transfer operations."""

    source_warehouse_id = fields.Int(required=True)
    destination_warehouse_id = fields.Int(required=True)
    item_id = fields.Int(required=True)
    quantity = fields.Float(required=True)
    notes = fields.Str(allow_none=True)

    @validates("quantity")
    def validate_quantity(self, value):
        """Validate transfer quantity is positive."""
        if value <= 0:
            raise ValidationError("Transfer quantity must be positive.")


class AuditLogSchema(Schema):
    """Schema for AuditLog model."""

    id = fields.Int(dump_only=True)
    type = fields.Str(dump_only=True)
    user_id = fields.Int(dump_only=True)
    item_id = fields.Int(dump_only=True)
    source_warehouse_id = fields.Int(dump_only=True)
    destination_warehouse_id = fields.Int(dump_only=True)
    quantity = fields.Float(dump_only=True)
    notes = fields.Str(dump_only=True)
    details_json = fields.Dict(dump_only=True)
    timestamp = fields.DateTime(dump_only=True)


# Schema instances
user_schema = UserSchema()
users_schema = UserSchema(many=True)
warehouse_schema = WarehouseSchema()
warehouses_schema = WarehouseSchema(many=True)
item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
transfer_schema = TransferSchema()
audit_log_schema = AuditLogSchema()
audit_logs_schema = AuditLogSchema(many=True)
