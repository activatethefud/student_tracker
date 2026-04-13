# AGENTS.md

## Project Context

Student tracker app: records grades, behavior, attendance via slash commands in a chat-like UI.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite
- **Frontend**: HTMX + TailwindCSS
- **PDF**: WeasyPrint
- **Deployment**: Docker

## Developer Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest

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