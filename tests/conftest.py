"""Test configuration and fixtures."""

import pytest
from app import create_app, db
from app.models import User, Warehouse, Item, Role


@pytest.fixture(scope="function")
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create admin user."""
    with app.app_context():
        user = User(username="admin", email="admin@test.com", role=Role.ADMIN.value)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "username": "admin"}


@pytest.fixture
def manager_user(app):
    """Create manager user."""
    with app.app_context():
        user = User(username="manager", email="manager@test.com", role=Role.MANAGER.value)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "username": "manager"}


@pytest.fixture
def viewer_user(app):
    """Create viewer user."""
    with app.app_context():
        user = User(username="viewer", email="viewer@test.com", role=Role.VIEWER.value)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "username": "viewer"}


@pytest.fixture
def sample_warehouse(app, admin_user):
    """Create sample warehouse (requires admin_user to ensure user is created first)."""
    with app.app_context():
        warehouse = Warehouse(
            name="Test Warehouse",
            code="WH-001",
            address="123 Test St",
            capacity=1000.0,
            contact_person="John Doe",
        )
        db.session.add(warehouse)
        db.session.commit()
        return {"id": warehouse.id, "code": warehouse.code}


@pytest.fixture
def sample_item(app, sample_warehouse):
    """Create sample item."""
    with app.app_context():
        item = Item(
            warehouse_id=sample_warehouse["id"],
            sku="ITEM-001",
            name="Test Item",
            description="A test item",
            quantity=100.0,
            unit="units",
        )
        db.session.add(item)
        db.session.commit()
        return {
            "id": item.id,
            "sku": item.sku,
            "warehouse_id": item.warehouse_id,
            "quantity": item.quantity,
        }


def login(client, username, password):
    """Helper function to log in."""
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    """Helper function to log out."""
    return client.get("/auth/logout", follow_redirects=True)
