# Student Tracker

A real-time student tracking application for recording grades, behavior, and attendance via a chat-like slash command interface.

## Features

- **Slash Commands** - Quick data entry: `/grade`, `/behavior`, `/attendance`, `/report`
- **Chat UI** - Simple, fast, mobile-friendly interface
- **JWT Authentication** - Secure access for teachers
- **SQLite Database** - Simple storage for up to 200 students
- **Docker Ready** - Easy deployment with Docker Compose

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite
- **Frontend**: HTMX + TailwindCSS
- **Deployment**: Docker

## Quick Start

### Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize admin user (first time)
curl -X POST http://localhost:8000/api/init-admin

# Run the app
uvicorn app.main:app --reload

# Open http://localhost:8000
# Login: admin / admin123
```

### Docker

```bash
docker compose up --build
```

## Slash Commands

| Command | Example | Description |
|---------|---------|-------------|
| `/add-student <name>` | `/add-student John` | Add new student |
| `/grade <name> <score>` | `/grade John 90 --subject Math` | Record grade |
| `/behavior <name> <type>` | `/behavior John positive --note "Helped peer"` | Record behavior |
| `/attendance <name> <status>` | `/attendance John present` | Mark attendance |
| `/report <name>` | `/report John` | Get student report |
| `/help` | `/help` | Show available commands |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/command` | Execute slash command |
| POST | `/api/init-admin` | Initialize admin user |
| POST | `/token` | Login (get JWT token) |
| GET | `/` | Main UI |
| GET | `/api/students` | List students (auth required) |
| GET | `/api/students/{name}/report` | Get student report |

## Project Structure

```
student_tracker/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── models.py       # SQLAlchemy models
│   ├── config.py       # Settings
│   └── commands.py     # Slash command parser
├── static/
│   └── index.html      # Chat UI
├── tests/              # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT