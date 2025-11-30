"""Tests for User model."""

import pytest
from app.models import User, Role


class TestUserModel:
    """Test User model."""

    def test_set_password(self, app):
        """Test password hashing."""
        with app.app_context():
            user = User(username="test", email="test@test.com")
            user.set_password("password123")
            assert user.password_hash is not None
            assert user.password_hash != "password123"

    def test_check_password(self, app):
        """Test password verification."""
        with app.app_context():
            user = User(username="test", email="test@test.com")
            user.set_password("password123")
            assert user.check_password("password123") is True
            assert user.check_password("wrongpassword") is False

    def test_has_role(self, app):
        """Test role checking."""
        with app.app_context():
            user = User(username="test", email="test@test.com", role=Role.ADMIN.value)
            assert user.has_role(Role.ADMIN) is True
            assert user.has_role(Role.MANAGER) is False

    def test_can_edit(self, app):
        """Test edit permission."""
        with app.app_context():
            admin = User(username="admin", email="admin@test.com", role=Role.ADMIN.value)
            manager = User(
                username="manager", email="manager@test.com", role=Role.MANAGER.value
            )
            viewer = User(
                username="viewer", email="viewer@test.com", role=Role.VIEWER.value
            )

            assert admin.can_edit() is True
            assert manager.can_edit() is True
            assert viewer.can_edit() is False

    def test_can_delete(self, app):
        """Test delete permission."""
        with app.app_context():
            admin = User(username="admin", email="admin@test.com", role=Role.ADMIN.value)
            manager = User(
                username="manager", email="manager@test.com", role=Role.MANAGER.value
            )

            assert admin.can_delete() is True
            assert manager.can_delete() is False
