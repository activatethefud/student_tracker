# AGENTS.md

## Project Context

Student tracker app: records grades, behavior, attendance via slash commands in a chat-like UI.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite
- **Frontend**: HTMX + TailwindCSS
- **PDF**: WeasyPrint
- **Deployment**: Docker

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete file dependency chain and how to update when adding new features.

### Quick Reference: What to Update

| Feature Type | Files to Update |
|--------------|-----------------|
| New slash command | `app/commands.py`, `app/main.py`, `static/index.html`, `tests/test_commands.py` |
| New API endpoint | `app/main.py`, `tests/test_api.py` |
| New page/template | `app/main.py`, `static/new.html`, `tests/test_frontend.py` |
| New data model | `app/models.py`, `app/main.py`, `app/pdf_generator.py`, `tests/test_api.py` |
| New export/import | `app/main.py`, `static/index.html`, `tests/test_api.py` |
| Frontend UI changes | `static/*.html`, `tests/test_frontend.py` |

## Developer Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest

# Run specific test
pytest tests/test_commands.py -v -k homework

# Run frontend template tests (catches Jinja2 errors)
pytest tests/test_frontend.py -v

# Docker
docker compose up --build
```

## Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Commit with conventional commits: `git commit -m "feat: add attendance tracking"`
3. Push and create PR: `git push -u origin feature/your-feature && gh pr create --fill`

## Remote

https://github.com/activatethefud/student_tracker

## Important Notes

- Repo is public - do not commit secrets/keys
- Use conventional commits (`feat:`, `fix:`, `docs:`)
- Test single: `pytest -k test_name`
- ALWAYS push commits to remote after completing changes: `git push origin main`
- **Backwards compatibility**: All changes must be backwards-compatible. Existing databases must continue to work without manual migration. New fields must have defaults. Import must handle exports from older versions (missing fields/keys). Always test import of older export formats.

## Reminder

After completing any task that involves code changes:
1. Run tests to verify the changes work
2. Commit the changes with a descriptive message
3. ALWAYS push to remote: `git push origin main`