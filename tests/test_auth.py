"""Tests for authentication routes."""

import pytest
from conftest import login, logout
from app import db
from app.models import User


class TestAuth:
    """Test authentication routes."""

    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get("/auth/register")
        assert response.status_code == 200
        assert b"Register" in response.data

    def test_successful_login(self, client, admin_user):
        """Test successful login."""
        response = login(client, "admin", "password123")
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_invalid_login(self, client, admin_user):
        """Test login with invalid credentials."""
        response = login(client, "admin", "wrongpassword")
        assert b"Invalid username or password" in response.data

    def test_logout(self, client, admin_user):
        """Test logout."""
        login(client, "admin", "password123")
        response = logout(client)
        assert response.status_code == 200
        assert b"You have been logged out" in response.data

    def test_successful_registration(self, client, app):
        """Test successful registration."""
        response = client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Registration successful" in response.data

        with app.app_context():
            user = User.query.filter_by(username="newuser").first()
            assert user is not None
            assert user.email == "newuser@test.com"

    def test_registration_duplicate_username(self, client, admin_user):
        """Test registration with existing username."""
        response = client.post(
            "/auth/register",
            data={
                "username": "admin",
                "email": "other@test.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert b"Username already exists" in response.data

    def test_protected_route_requires_login(self, client):
        """Test that protected routes require login."""
        response = client.get("/dashboard", follow_redirects=True)
        assert b"Please log in" in response.data
