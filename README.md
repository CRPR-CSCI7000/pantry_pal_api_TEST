# PantryPal Django Backend

Refactored from Flask to Django REST Framework.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in your values
python manage.py migrate
python manage.py runserver 5001
```

## Apps

| App | Endpoints |
|-----|-----------|
| `auth_app` | `POST /api/signup`, `POST /api/login`, `POST /api/token/refresh` |
| `products` | `GET /api/lookup-upc`, `POST /api/products`, `GET /api/products/<upc>` |
| `pantry` | `GET/POST /api/pantry`, `PUT/DELETE /api/pantry/<id>`, `GET /api/pantry/product/<upc>` |
| `recipes` | `POST /api/get-recipes`, `POST /api/cook-recipe` |

## Key Differences from Flask

- JWT tokens are issued by `djangorestframework-simplejwt` (still `Bearer` scheme — frontend unchanged)
- Custom `User` model replaces raw psycopg2 queries
- `PantryItem` model replaces the `usersProducts` table queries
- `Product` model replaces direct SQL inserts
- `pantrypal/services/email_service.py` fires events to `pantrypal-email-worker` on pantry mutations

## Event Schema

Pantry mutations emit events to the email worker using the envelope schema in `services/email_service.py`:

```json
{
  "schema_version": "1.0.0",
  "event_type": "pantry.item.added",
  "occurred_at": "2025-01-01T00:00:00+00:00",
  "payload": { ... }
}
```
