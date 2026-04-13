# Student Tracker

A real-time student tracking application for recording grades, behavior, and attendance via a chat-like slash command interface.

## Features

- **Slash Commands** - Quick data entry: `/grade`, `/behavior`, `/attendance`, `/homework`, `/report`
- **Homework Tracking** - Track assignments with due dates and status (pending/submitted)
- **Autocomplete** - Smart suggestions for commands, student names, subjects, and options
- **Date/Time Support** - Add historical records with `--date YYYY-MM-DD`
- **PDF Reports** - Generate downloadable PDF reports with `--pdf`
- **Chat UI** - Simple, fast, mobile-friendly interface with login
- **JWT Authentication** - Secure access for teachers
- **First-Time Setup** - Built-in admin creation screen for new installations
- **SQLite Database** - Simple storage for up to 200 students
- **Docker Ready** - Easy deployment with Docker Compose

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite
- **Frontend**: HTMX + TailwindCSS
- **PDF Generation**: WeasyPrint
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

# Run the app
uvicorn app.main:app --reload

# Open http://localhost:8000
# First visit /setup to create admin account
```

### Docker

```bash
docker compose up --build
```

## First-Time Setup

1. Visit `http://localhost:8000/setup`
2. Create your admin username and password
3. Login with those credentials

## Slash Commands

| Command | Example | Description |
|---------|---------|-------------|
| `/add-student <name>` | `/add-student John` | Add new student |
| `/grade <name> <score>` | `/grade John 90 --subject Math` | Record grade |
| `/grade John 90 --date 2024-03-15` | Grade with custom date |
| `/behavior <name> <type>` | `/behavior John positive --note "Helped peer"` | Record behavior |
| `/behavior John positive --date 2024-03-20` | Behavior with custom date |
| `/attendance <name> <status>` | `/attendance John present` | Mark attendance |
| `/attendance John late --date 2024-03-10` | Attendance with custom date |
| `/homework <name> <title>` | `/homework John "Read chapter 5"` | Add homework |
| `/homework John "Math hw" --due 2024-04-15` | Homework with due date |
| `/homework John "Essay" --status submitted` | Mark homework as submitted |
| `/report <name>` | `/report John` | Get student report |
| `/report John --from 2024-01-01 --to 2024-12-31` | Report with date range |
| `/report John --pdf` | Download PDF report |
| `/help` | `/help` | Show available commands |

### Date Options

- `--date YYYY-MM-DD` - Set specific date for a record
- `--from YYYY-MM-DD` - Filter report from date (report only)
- `--to YYYY-MM-DD` - Filter report to date (report only)
- `--pdf` - Generate PDF download (report only)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main UI |
| GET | `/setup` | First-time admin setup |
| POST | `/token` | Login (get JWT token) |
| POST | `/api/init-admin` | Initialize admin user |
| POST | `/api/command` | Execute slash command (auth required) |
| GET | `/api/students` | List students (auth required) |
| GET | `/api/autocomplete` | Autocomplete suggestions (auth required) |
| GET | `/api/students/{name}/report` | Get JSON report |
| POST | `/api/students/{name}/report/pdf` | Download PDF report |

## Project Structure

```
student_tracker/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── models.py        # SQLAlchemy models
│   ├── config.py        # Settings
│   ├── commands.py      # Slash command parser
│   └── pdf_generator.py # PDF report generation
├── static/
│   ├── index.html       # Chat UI
│   └── setup.html       # Admin setup screen
├── tests/               # Test suite
│   ├── test_commands.py
│   ├── test_api.py
│   └── test_auth.py
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