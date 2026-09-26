# Inventory Reporting Web Application

A production-oriented inventory reporting application built with FastAPI, SQLAlchemy, SQLite for the initial deployment, and a clean modular architecture ready for PostgreSQL migration.

## Features

- Secure login with session-based authentication
- Admin role support
- Excel upload with validation and bulk replacement
- High-volume inventory import support (200k+ rows)
- Reports with server-side pagination, sorting, and filtering
- Excel export for filtered results
- Modern Bootstrap 5 UI with responsive design
- SQLite-first database with future PostgreSQL migration readiness

## Technology Stack

- Backend: FastAPI
- ORM: SQLAlchemy
- Database: SQLite (current), PostgreSQL compatible design
- Frontend: Bootstrap 5 + JavaScript + HTML5
- Excel: Pandas + OpenPyXL
- Authentication: Session-based login

## Project Structure

```text
REPORT_TOOL/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── inventory.py
│   │       ├── reports.py
│   │       └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── inventory.py
│   │   ├── upload_history.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── inventory_repository.py
│   │   ├── upload_history_repository.py
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── inventory.py
│   │   └── report.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── export_service.py
│   │   ├── report_service.py
│   │   └── upload_service.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── master_uploader.html
│       └── reports.html
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
├── inventory.db (created at runtime)
└── README.md
```

## Database Schema

The application creates the following tables automatically:

- Users
  - id
  - username
  - password_hash
  - role
  - created_date
- Inventory_Master
  - id
  - main_code
  - child_code
  - description
  - available_qty
  - set_qty
  - loose_qty
  - upload_batch_id
  - created_date
- Upload_History
  - batch_id
  - file_name
  - uploaded_by
  - upload_date
  - total_records
  - success_records
  - failed_records
  - status

Indexes are applied for:

- main_code
- child_code
- description

## Default Login

- Username: admin
- Password: admin123

## Running the Application

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open the browser:

```text
http://localhost:8000/login
```

## Upload Logic

- Validates required columns before import
- Reads Excel data using Pandas and OpenPyXL
- Replaces the entire inventory table for each new upload
- Stores batch metadata in upload history
- Uses transactional replacement for consistency and rollback safety
- Keeps the design compatible with future background processing workers

## Report Behavior

- Paginated server-side result set
- Maximum 100 records per page
- Filtering on Main Code, Child Code, and Description
- Sorting across all reportable columns
- Excel export preserves current filters and sort order

## Security Highlights

- Bcrypt password hashing
- Session-based user authentication
- Protected routes using server-side session checks
- Input validation and SQLAlchemy ORM safeguards
- SQLite default for local deployment, while application patterns remain PostgreSQL-ready

## Future PostgreSQL Migration Approach

To move from SQLite to PostgreSQL without a large refactor:

1. Add a PostgreSQL connection string in the environment variables, for example:

```env
DATABASE_URL_POSTGRESQL=postgresql+psycopg2://app_user:app_password@localhost:5432/inventory_db
```

2. Keep the SQLAlchemy models unchanged and switch the engine configuration through settings.
3. Use Alembic for schema versioning and migrations.
4. Validate data types and column names before switching production workloads.
5. Re-run the application with PostgreSQL credentials and verify performance, indexes, and transactional behavior.
6. For large imports, move the Excel processing into a background worker or queue system and keep the web process lightweight.

Recommended migration stack:

- Alembic
- PostgreSQL
- psycopg2-binary
- background workers such as Celery/RQ in a later phase

## Notes

This solution is intentionally structured for enterprise inventory operations and is optimized for maintainability, security, and resource-friendly reporting.
