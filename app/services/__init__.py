"""Service layer for business logic."""

from app import db
from app.models import Warehouse, Item, AuditLog, AuditType


class WarehouseService:
    """Service for warehouse operations."""

    @staticmethod
    def get_all(search=None, filters=None):
        """Get all warehouses with optional filtering."""
        query = Warehouse.query

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Warehouse.name.ilike(search_term),
                    Warehouse.code.ilike(search_term),
                    Warehouse.address.ilike(search_term),
                )
            )

        if filters:
            if filters.get("capacity_min"):
                query = query.filter(
                    Warehouse.capacity >= filters["capacity_min"]
                )
            if filters.get("capacity_max"):
                query = query.filter(
                    Warehouse.capacity <= filters["capacity_max"]
                )

        return query.order_by(Warehouse.name).all()

    @staticmethod
    def get_by_id(warehouse_id):
        """Get a warehouse by ID."""
        return db.session.get(Warehouse, warehouse_id)

    @staticmethod
    def get_by_code(code):
        """Get a warehouse by code."""
        return Warehouse.query.filter_by(code=code).first()

    @staticmethod
    def create(data, user=None):
        """Create a new warehouse."""
        warehouse = Warehouse(
            name=data["name"],
            code=data["code"],
            address=data.get("address"),
            capacity=data.get("capacity"),
            contact_person=data.get("contact_person"),
            notes=data.get("notes"),
            metadata_json=data.get("metadata_json", {}),
        )
        db.session.add(warehouse)
        db.session.commit()

        # Log the creation
        AuditService.log(
            audit_type=AuditType.CREATE,
            user=user,
            notes=f"Created warehouse: {warehouse.code}",
            details={"warehouse_id": warehouse.id, "name": warehouse.name},
        )

        return warehouse

    @staticmethod
    def update(warehouse, data, user=None):
        """Update an existing warehouse."""
        old_values = {
            "name": warehouse.name,
            "code": warehouse.code,
            "address": warehouse.address,
        }

        for key in ["name", "code", "address", "capacity",
                    "contact_person", "notes", "metadata_json"]:
            if key in data:
                setattr(warehouse, key, data[key])

        db.session.commit()

        # Log the update
        AuditService.log(
            audit_type=AuditType.UPDATE,
            user=user,
            notes=f"Updated warehouse: {warehouse.code}",
            details={
                "warehouse_id": warehouse.id,
                "old_values": old_values,
                "new_values": data,
            },
        )

        return warehouse

    @staticmethod
    def delete(warehouse, user=None):
        """Delete a warehouse."""
        # Check if warehouse has items
        if warehouse.items.count() > 0:
            raise ValueError("Cannot delete warehouse with items")

        warehouse_info = {"id": warehouse.id, "code": warehouse.code}
        db.session.delete(warehouse)
        db.session.commit()

        # Log the deletion
        AuditService.log(
            audit_type=AuditType.DELETE,
            user=user,
            notes=f"Deleted warehouse: {warehouse_info['code']}",
            details=warehouse_info,
        )


class ItemService:
    """Service for item operations."""

    @staticmethod
    def get_all(warehouse_id=None, search=None, filters=None):
        """Get all items with optional filtering."""
        query = Item.query

        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Item.name.ilike(search_term),
                    Item.sku.ilike(search_term),
                    Item.description.ilike(search_term),
                )
            )

        if filters:
            if filters.get("low_stock"):
                query = query.filter(Item.quantity <= filters["low_stock"])
            if filters.get("batch_number"):
                query = query.filter_by(batch_number=filters["batch_number"])

        return query.order_by(Item.name).all()

    @staticmethod
    def get_by_id(item_id):
        """Get an item by ID."""
        return db.session.get(Item, item_id)

    @staticmethod
    def create(data, user=None):
        """Create a new item."""
        item = Item(
            warehouse_id=data["warehouse_id"],
            sku=data["sku"],
            name=data["name"],
            description=data.get("description"),
            quantity=data.get("quantity", 0),
            unit=data.get("unit", "units"),
            batch_number=data.get("batch_number"),
            expiry_date=data.get("expiry_date"),
            metadata_json=data.get("metadata_json", {}),
        )
        db.session.add(item)
        db.session.commit()

        # Log the creation
        AuditService.log(
            audit_type=AuditType.ADD,
            user=user,
            item_id=item.id,
            source_warehouse_id=item.warehouse_id,
            quantity=item.quantity,
            notes=f"Added item: {item.sku}",
            details={"name": item.name},
        )

        return item

    @staticmethod
    def update(item, data, user=None):
        """Update an existing item."""
        old_quantity = item.quantity

        for key in ["name", "description", "quantity", "unit",
                    "batch_number", "expiry_date", "metadata_json"]:
            if key in data:
                setattr(item, key, data[key])

        db.session.commit()

        # Log quantity changes
        if "quantity" in data and data["quantity"] != old_quantity:
            AuditService.log(
                audit_type=AuditType.UPDATE,
                user=user,
                item_id=item.id,
                source_warehouse_id=item.warehouse_id,
                quantity=data["quantity"] - old_quantity,
                notes=f"Updated quantity for {item.sku}",
                details={
                    "old_quantity": old_quantity,
                    "new_quantity": data["quantity"],
                },
            )

        return item

    @staticmethod
    def delete(item, user=None):
        """Delete an item."""
        item_info = {
            "id": item.id,
            "sku": item.sku,
            "warehouse_id": item.warehouse_id,
        }
        db.session.delete(item)
        db.session.commit()

        # Log the deletion
        AuditService.log(
            audit_type=AuditType.REMOVE,
            user=user,
            item_id=item_info["id"],
            source_warehouse_id=item_info["warehouse_id"],
            notes=f"Removed item: {item_info['sku']}",
            details=item_info,
        )

    @staticmethod
    def transfer(source_warehouse_id, destination_warehouse_id, item_id,
                 quantity, user=None, notes=None):
        """Transfer items between warehouses."""
        source_item = Item.query.filter_by(
            warehouse_id=source_warehouse_id, id=item_id
        ).first()

        if not source_item:
            raise ValueError("Item not found in source warehouse")

        if source_item.quantity < quantity:
            raise ValueError("Insufficient quantity for transfer")

        # Check if item exists in destination
        dest_item = Item.query.filter_by(
            warehouse_id=destination_warehouse_id, sku=source_item.sku
        ).first()

        # Decrease source quantity
        source_item.quantity -= quantity

        if dest_item:
            # Add to existing item in destination
            dest_item.quantity += quantity
        else:
            # Create new item in destination
            dest_item = Item(
                warehouse_id=destination_warehouse_id,
                sku=source_item.sku,
                name=source_item.name,
                description=source_item.description,
                quantity=quantity,
                unit=source_item.unit,
                batch_number=source_item.batch_number,
                expiry_date=source_item.expiry_date,
                metadata_json=source_item.metadata_json.copy()
                if source_item.metadata_json else {},
            )
            db.session.add(dest_item)

        db.session.commit()

        # Log the transfer
        AuditService.log(
            audit_type=AuditType.TRANSFER,
            user=user,
            item_id=source_item.id,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            quantity=quantity,
            notes=notes or f"Transferred {quantity} {source_item.unit} of {source_item.sku}",
            details={
                "sku": source_item.sku,
                "source_remaining": source_item.quantity,
                "destination_quantity": dest_item.quantity,
            },
        )

        return {"source_item": source_item, "destination_item": dest_item}


class AuditService:
    """Service for audit log operations."""

    @staticmethod
    def log(audit_type, user=None, item_id=None, source_warehouse_id=None,
            destination_warehouse_id=None, quantity=None, notes=None,
            details=None):
        """Create an audit log entry."""
        entry = AuditLog(
            type=audit_type.value if isinstance(audit_type, AuditType) else audit_type,
            user_id=user.id if user else None,
            item_id=item_id,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            quantity=quantity,
            notes=notes,
            details_json=details or {},
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @staticmethod
    def get_logs(page=1, per_page=50, filters=None):
        """Get audit logs with pagination and optional filtering."""
        query = AuditLog.query

        if filters:
            if filters.get("type"):
                query = query.filter_by(type=filters["type"])
            if filters.get("user_id"):
                query = query.filter_by(user_id=filters["user_id"])
            if filters.get("warehouse_id"):
                query = query.filter(
                    db.or_(
                        AuditLog.source_warehouse_id == filters["warehouse_id"],
                        AuditLog.destination_warehouse_id == filters["warehouse_id"],
                    )
                )

        return query.order_by(AuditLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
