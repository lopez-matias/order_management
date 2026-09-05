# Contributing

Thank you for your interest in improving NODO. This document describes the expected local workflow and the checks a contribution should pass before review.

## Development setup

1. Fork or clone the repository.
2. Create a Python 3.12+ virtual environment.
3. Install the dependencies from `requirements.txt`.
4. Copy `.env.example` to `.env` and configure PostgreSQL.
5. Apply migrations and load the fictional demo dataset.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m scripts.seed_demo
```

Start the development server with:

```bash
uvicorn app.main:app --reload
```

## Code guidelines

- Use English for source-code identifiers, comments, docstrings, commits, and developer documentation.
- Keep the end-user interface in Spanish unless a localization feature is being introduced.
- Put business rules in `app/services` rather than duplicating them in route handlers or browser code.
- Use SQLAlchemy 2-style queries and typed mappings.
- Use Pydantic schemas for every public request and response contract.
- Use `Decimal` for monetary operations.
- Do not accept calculated prices or totals from clients.
- Preserve historical records and existing soft-deletion behavior.
- Do not add Node.js or a frontend build requirement.

## Tests

Every behavioral change should include or update tests.

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

Tests must be deterministic and must not depend on external services or real personal data.

## Database changes

Model changes require a matching Alembic revision. Generate and review it locally:

```bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
alembic check
```

Verify both upgrade and downgrade behavior when the change is reversible. Never rewrite a migration that may already have been applied outside your branch.

## Demo data

Demo records must remain explicitly fictional:

- Use generic customer names prefixed with `Demo` where practical.
- Use `.test` email domains.
- Use clearly synthetic documents and references.
- Never include real contact information or claim real business performance.
- Keep the seed idempotent.

## Pull requests

A pull request should contain:

- A concise explanation of the problem and solution.
- Any relevant API or UI screenshots.
- Tests for new or changed behavior.
- A migration when the database schema changes.
- Updated English documentation when public behavior changes.

Keep pull requests focused. Avoid unrelated formatting or dependency changes.

