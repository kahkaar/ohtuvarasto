"""Database models for the warehouse application."""

from datetime import datetime, timezone
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class Role(Enum):
    """User roles for access control."""

    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


class AuditType(Enum):
    """Types of audit log entries."""

    ADD = "add"
    REMOVE = "remove"
    TRANSFER = "transfer"
    UPDATE = "update"
    CREATE = "create"
    DELETE = "delete"


class User(UserMixin, db.Model):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default=Role.VIEWER.value, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        """Check if user has the specified role."""
        if isinstance(role, Role):
            role = role.value
        return self.role == role

    def can_edit(self):
        """Check if user can edit resources."""
        return self.role in [Role.ADMIN.value, Role.MANAGER.value]

    def can_delete(self):
        """Check if user can delete resources."""
        return self.role == Role.ADMIN.value

    def __repr__(self):
        return f"<User {self.username}>"


class Warehouse(db.Model):
    """Warehouse model for storage locations."""

    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(255))
    capacity = db.Column(db.Float)
    contact_person = db.Column(db.String(100))
    notes = db.Column(db.Text)
    metadata_json = db.Column(db.JSON, default=dict)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    items = db.relationship(
        "Item", backref="warehouse", lazy="dynamic", cascade="all, delete-orphan"
    )

    def get_total_quantity(self):
        """Get total quantity of all items in this warehouse."""
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<Warehouse {self.code}: {self.name}>"


class Item(db.Model):
    """Item model for inventory entries."""

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(
        db.Integer, db.ForeignKey("warehouses.id"), nullable=False
    )
    sku = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Float, default=0.0, nullable=False)
    unit = db.Column(db.String(20), default="units")
    batch_number = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    metadata_json = db.Column(db.JSON, default=dict)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Unique constraint for SKU within a warehouse
    __table_args__ = (
        db.UniqueConstraint("warehouse_id", "sku", name="unique_warehouse_sku"),
    )

    def __repr__(self):
        return f"<Item {self.sku}: {self.name}>"


class AuditLog(db.Model):
    """Audit log model for tracking changes."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    item_id = db.Column(db.Integer)
    source_warehouse_id = db.Column(db.Integer)
    destination_warehouse_id = db.Column(db.Integer)
    quantity = db.Column(db.Float)
    notes = db.Column(db.Text)
    details_json = db.Column(db.JSON, default=dict)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<AuditLog {self.type} at {self.timestamp}>"
