# Student Tracker

A real-time student tracking application for recording grades, behavior, and attendance via a chat-like slash command interface.

## Features

- **Slash Commands** - Quick data entry: `/grade`, `/behavior`, `/attendance`
- **PDF Reports** - Generate student summary reports with stats
- **Chat UI** - Simple, fast, mobile-friendly interface
- **JWT Authentication** - Secure access for teachers

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite (up to 200 students)
- **Frontend**: HTMX + TailwindCSS
- **PDF Generation**: WeasyPrint
- **Deployment**: Docker + Docker Compose

## Quick Start

### Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --reload

# Open http://localhost:8000
```

### Docker

```bash
docker compose up --build
```

## Slash Commands

| Command | Example | Description |
|---------|---------|-------------|
| `/grade <name> <score>` | `/grade John 90` | Record grade |
| `/behavior <name> <note>` | `/behavior John positive` | Record behavior |
| `/attendance <name> present` | `/attendance John present` | Mark attendance |
| `/add-student <name>` | `/add-student John` | Add new student |
| `/report <name>` | `/report John` | Generate PDF report |

## Project Structure

```
student_tracker/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── models.py       # SQLAlchemy models
│   ├── routes.py      # API routes
│   └── commands.py   # Slash command parser
├── static/            # HTMX templates
├── tests/             # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT