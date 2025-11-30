# ohtuvarasto

[![CI](https://github.com/kahkaar/ohtuvarasto/actions/workflows/main.yml/badge.svg)](https://github.com/kahkaar/ohtuvarasto/actions/workflows/main.yml) [![codecov](https://codecov.io/github/kahkaar/ohtuvarasto/graph/badge.svg?token=OOHXR0RR2M)](https://codecov.io/github/kahkaar/ohtuvarasto)

A warehouse management system built with Python and Flask.

## Features

- **Multiple Warehouses**: Create and manage multiple storage locations with detailed information
- **Inventory Tracking**: Track items, quantities, batch numbers, and expiry dates
- **Item Transfers**: Move items between warehouses with full audit trail
- **Low Stock Alerts**: Get notified when items are running low
- **User Management**: Role-based access control (Admin, Manager, Viewer)
- **REST API**: Full API for integration with other systems
- **Responsive UI**: Works on desktop and mobile devices

## Quick Start

### Local Development (without Docker)

1. Install dependencies:
```bash
pip install poetry
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the application:
```bash
poetry run flask run
```

4. Open http://localhost:5000 in your browser

### Docker Development

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Open http://localhost:8000 in your browser

### Production Docker Build

1. Build the image:
```bash
docker build -t warehouse-app:latest .
```

2. Run with environment variables:
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your-secure-secret-key \
  warehouse-app:latest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | Database connection string | sqlite:///warehouse.db |
| `SECRET_KEY` | Secret key for sessions | dev-secret-key |

## API Endpoints

### Warehouses
- `GET /api/warehouses` - List all warehouses
- `POST /api/warehouses` - Create a warehouse
- `GET /api/warehouses/{id}` - Get a warehouse
- `PUT /api/warehouses/{id}` - Update a warehouse
- `DELETE /api/warehouses/{id}` - Delete a warehouse

### Items
- `GET /api/warehouses/{id}/items` - List items in a warehouse
- `POST /api/warehouses/{id}/items` - Add an item
- `GET /api/warehouses/{id}/items/{item_id}` - Get an item
- `PUT /api/warehouses/{id}/items/{item_id}` - Update an item
- `DELETE /api/warehouses/{id}/items/{item_id}` - Delete an item

### Transfers & Audit
- `POST /api/transfers` - Transfer items between warehouses
- `GET /api/audit` - View audit logs

## User Roles

- **Admin**: Full access to all features including user management
- **Manager**: Can create, edit warehouses and items, transfer items
- **Viewer**: Read-only access to warehouses and items

## Testing

Run the test suite:
```bash
poetry run pytest
```

With coverage:
```bash
poetry run coverage run --branch -m pytest
poetry run coverage report
```

## Project Structure

```
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   ├── config.py          # Configuration
│   ├── models.py          # Database models
│   ├── routes/            # Route blueprints
│   │   ├── api.py         # REST API
│   │   ├── auth.py        # Authentication
│   │   ├── items.py       # Item management
│   │   ├── main.py        # Main pages
│   │   └── warehouses.py  # Warehouse management
│   ├── schemas/           # Marshmallow schemas
│   ├── services/          # Business logic
│   ├── static/            # CSS, JS
│   └── templates/         # Jinja2 templates
├── src/                   # Original varasto module
├── tests/                 # Test files
├── Dockerfile             # Production Docker image
├── docker-compose.yml     # Development setup
└── pyproject.toml         # Dependencies
```
