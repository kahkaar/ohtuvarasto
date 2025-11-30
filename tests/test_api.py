"""Tests for REST API endpoints."""

import pytest
import json
from conftest import login


class TestWarehouseAPI:
    """Test warehouse API endpoints."""

    def test_list_warehouses_requires_auth(self, client):
        """Test that listing warehouses requires authentication."""
        response = client.get("/api/warehouses")
        assert response.status_code == 302  # Redirect to login

    def test_list_warehouses(self, client, admin_user):
        """Test listing warehouses."""
        login(client, "admin", "password123")
        response = client.get("/api/warehouses")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_create_warehouse(self, client, admin_user):
        """Test creating a warehouse."""
        login(client, "admin", "password123")
        response = client.post(
            "/api/warehouses",
            data=json.dumps({"name": "New Warehouse", "code": "WH-NEW"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "New Warehouse"
        assert data["code"] == "WH-NEW"

    def test_create_warehouse_duplicate_code(self, client, admin_user, sample_warehouse):
        """Test creating warehouse with duplicate code."""
        login(client, "admin", "password123")
        response = client.post(
            "/api/warehouses",
            data=json.dumps({"name": "Another Warehouse", "code": "WH-001"}),
            content_type="application/json",
        )
        assert response.status_code == 409

    def test_get_warehouse(self, client, admin_user, sample_warehouse):
        """Test getting a specific warehouse."""
        login(client, "admin", "password123")
        response = client.get(f"/api/warehouses/{sample_warehouse['id']}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["code"] == "WH-001"

    def test_get_warehouse_not_found(self, client, admin_user):
        """Test getting a non-existent warehouse."""
        login(client, "admin", "password123")
        response = client.get("/api/warehouses/9999")
        assert response.status_code == 404

    def test_update_warehouse(self, client, admin_user, sample_warehouse):
        """Test updating a warehouse."""
        login(client, "admin", "password123")
        response = client.put(
            f"/api/warehouses/{sample_warehouse['id']}",
            data=json.dumps({"name": "Updated Warehouse"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Warehouse"

    def test_delete_warehouse(self, client, admin_user, sample_warehouse):
        """Test deleting a warehouse."""
        login(client, "admin", "password123")
        response = client.delete(f"/api/warehouses/{sample_warehouse['id']}")
        assert response.status_code == 204

    def test_viewer_cannot_create_warehouse(self, client, viewer_user):
        """Test that viewers cannot create warehouses."""
        login(client, "viewer", "password123")
        response = client.post(
            "/api/warehouses",
            data=json.dumps({"name": "New Warehouse", "code": "WH-NEW"}),
            content_type="application/json",
        )
        assert response.status_code == 403


class TestItemAPI:
    """Test item API endpoints."""

    def test_list_items(self, client, admin_user, sample_warehouse):
        """Test listing items in a warehouse."""
        login(client, "admin", "password123")
        response = client.get(f"/api/warehouses/{sample_warehouse['id']}/items")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_create_item(self, client, admin_user, sample_warehouse):
        """Test creating an item."""
        login(client, "admin", "password123")
        response = client.post(
            f"/api/warehouses/{sample_warehouse['id']}/items",
            data=json.dumps(
                {
                    "sku": "NEW-001",
                    "name": "New Item",
                    "quantity": 50,
                    "warehouse_id": sample_warehouse["id"],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["sku"] == "NEW-001"

    def test_get_item(self, client, admin_user, sample_item):
        """Test getting a specific item."""
        login(client, "admin", "password123")
        response = client.get(
            f"/api/warehouses/{sample_item['warehouse_id']}/items/{sample_item['id']}"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["sku"] == "ITEM-001"

    def test_update_item(self, client, admin_user, sample_item):
        """Test updating an item."""
        login(client, "admin", "password123")
        response = client.put(
            f"/api/warehouses/{sample_item['warehouse_id']}/items/{sample_item['id']}",
            data=json.dumps({"quantity": 150}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["quantity"] == 150

    def test_delete_item(self, client, admin_user, sample_item):
        """Test deleting an item."""
        login(client, "admin", "password123")
        response = client.delete(
            f"/api/warehouses/{sample_item['warehouse_id']}/items/{sample_item['id']}"
        )
        assert response.status_code == 204


class TestTransferAPI:
    """Test transfer API endpoint."""

    def test_transfer_item(self, client, admin_user, sample_item, app):
        """Test transferring an item between warehouses."""
        from app import db
        from app.models import Warehouse

        with app.app_context():
            # Create destination warehouse
            dest = Warehouse(name="Destination", code="WH-DEST")
            db.session.add(dest)
            db.session.commit()
            dest_id = dest.id

        login(client, "admin", "password123")
        response = client.post(
            "/api/transfers",
            data=json.dumps(
                {
                    "source_warehouse_id": sample_item["warehouse_id"],
                    "destination_warehouse_id": dest_id,
                    "item_id": sample_item["id"],
                    "quantity": 25,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Transfer successful"

    def test_transfer_insufficient_quantity(
        self, client, admin_user, sample_item, app
    ):
        """Test transfer with insufficient quantity."""
        from app import db
        from app.models import Warehouse

        with app.app_context():
            dest = Warehouse(name="Destination", code="WH-DEST")
            db.session.add(dest)
            db.session.commit()
            dest_id = dest.id

        login(client, "admin", "password123")
        response = client.post(
            "/api/transfers",
            data=json.dumps(
                {
                    "source_warehouse_id": sample_item["warehouse_id"],
                    "destination_warehouse_id": dest_id,
                    "item_id": sample_item["id"],
                    "quantity": 1000,  # More than available
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestAuditAPI:
    """Test audit log API endpoint."""

    def test_list_audit_logs(self, client, admin_user):
        """Test listing audit logs."""
        login(client, "admin", "password123")
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert "total" in data
