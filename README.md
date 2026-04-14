# Student Tracker

A student tracking application for recording grades, behavior, attendance, homework, activity, and progress via a chat-like slash command interface.

## Features

- **Slash Commands** — Quick data entry for all record types
- **Student Dashboard** — View and edit all records for a student in one page
- **Activity Tracking** — Record any activity type with yes/no status
- **Progress Tracking** — Record numerical checkpoints for any goal
- **Homework Tracking** — Track assignments with due dates and status
- **PDF Reports** — Download styled PDF reports with charts
- **Data Export/Import** — Full JSON export and import with merge or replace modes
- **Chat UI** — Simple, fast, mobile-friendly interface
- **JWT Authentication** — Secure login with HttpOnly cookie for page routes
- **First-Time Setup** — Built-in admin account creation on first visit
- **Master Password Reset** — Recover from locked accounts or forgotten passwords
- **Docker Ready** — Easy deployment with Docker Compose

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite
- **Frontend**: TailwindCSS (no build step)
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

# Run the development server
uvicorn app.main:app --reload

# Open http://localhost:8000
```

On first visit, you'll be prompted to create an admin account.

### Docker

```bash
docker compose up --build
```

The app runs on port 8000. Data is persisted in `./data/student_tracker.db`.

## First-Time Setup

1. Visit `http://localhost:8000`
2. Click the setup link to create an admin username and password (minimum 6 characters)
3. Log in with those credentials

If you forget your password or get locked out after 3 failed attempts, use the "Reset with master password" option. The default master password is configured in `docker-compose.yml` or `.env`.

## Slash Commands

| Command | Example | Description |
|---------|---------|-------------|
| `/add-student <name>` | `/add-student John --year "Grade 8"` | Add new student |
| `/grade <name> <score>` | `/grade John 90 --subject Math` | Record grade |
| `/grade John 90 --date 2024-03-15` | | Grade with custom date |
| `/behavior <name> <type>` | `/behavior John positive --note "Helped peer"` | Record behavior (positive/negative/neutral) |
| `/attendance <name> <status>` | `/attendance John present` | Mark attendance (present/absent/late) |
| `/homework <name> <title>` | `/homework John "Read chapter 5"` | Add homework |
| `/homework John "Math hw" --due 2024-04-15` | | Homework with due date |
| `/activity <name> <type> <status>` | `/activity John focus yes` | Record activity (any type, yes/no) |
| `/progress <name> <goal> <value>` | `/progress John running 3.5` | Record progress checkpoint |
| `/progress John weight 72.5 --date 2024-04-10` | | Progress with custom date |
| `/report <name>` | `/report John` | Get student report |
| `/report John --from 2024-01-01 --to 2024-12-31` | | Report with date range |
| `/report John --pdf` | | Download PDF report |
| `/dashboard <name>` | `/dashboard John` | Open student dashboard |
| `/dashboard` | | List all students |
| `/help` | `/help` | Show available commands |

### Date Options

- `--date YYYY-MM-DD` — Set specific date for a record (works with most commands)
- `--from YYYY-MM-DD` — Filter report from date (report only)
- `--to YYYY-MM-DD` — Filter report to date (report only)
- `--due YYYY-MM-DD` — Set due date for homework
- `--pdf` — Generate PDF download (report only)

### Multi-Word Names

All commands support multi-word student names:

```
/grade "Marko Stefanovic" 90
/attendance "Ana Marie" present
```

## Student Dashboard

Visit `/students` to see all students, or use `/dashboard <name>` to open a student's detail page. The dashboard shows:

- Summary cards (average grade, attendance rate, pending homework)
- Grades, behaviors, attendance, homework, activities, and progress tables
- Inline editing and deleting for each record
- Download PDF button

## Data Export & Import

Two buttons appear in the header when logged in:

- **Export** — Downloads a JSON file containing all student data
- **Import** — Upload a JSON file. Two modes:
  - **Replace** (default) — Deletes all existing student data, then imports the file
  - **Merge** — Keeps existing students and adds new ones. For students with the same name, their records are merged in

The export format includes a `version` field for forwards compatibility. Importing an older export (e.g., one without progress records) works cleanly — missing fields default to empty.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | No | Main chat UI |
| GET | `/setup` | No | First-time admin setup page |
| GET | `/students` | Cookie | List all students |
| GET | `/student/{name}` | Cookie | Student dashboard |
| POST | `/token` | No | Login (returns JWT + sets cookie) |
| POST | `/api/setup-admin` | No | Create first admin account |
| GET | `/api/setup-status` | No | Check if setup is needed |
| POST | `/api/command` | Bearer | Execute slash command |
| GET | `/api/students` | Bearer | List students (JSON) |
| POST | `/api/students` | Bearer | Create student |
| PUT | `/api/students/{name}` | Bearer | Update student |
| DELETE | `/api/students/{name}` | Bearer | Delete student (cascade) |
| POST | `/api/grades` | Bearer | Add grade |
| PUT | `/api/grades/{id}` | Bearer | Update grade |
| DELETE | `/api/grades/{id}` | Bearer | Delete grade |
| POST | `/api/behaviors` | Bearer | Add behavior |
| PUT | `/api/behaviors/{id}` | Bearer | Update behavior |
| DELETE | `/api/behaviors/{id}` | Bearer | Delete behavior |
| POST | `/api/attendance` | Bearer | Add attendance |
| PUT | `/api/attendance/{id}` | Bearer | Update attendance |
| DELETE | `/api/attendance/{id}` | Bearer | Delete attendance |
| POST | `/api/homework` | Bearer | Add homework |
| PUT | `/api/homework/{id}` | Bearer | Update homework |
| DELETE | `/api/homework/{id}` | Bearer | Delete homework |
| POST | `/api/activities` | Bearer | Add activity |
| PUT | `/api/activities/{id}` | Bearer | Update activity |
| DELETE | `/api/activities/{id}` | Bearer | Delete activity |
| POST | `/api/progress` | Bearer | Add progress |
| PUT | `/api/progress/{id}` | Bearer | Update progress |
| DELETE | `/api/progress/{id}` | Bearer | Delete progress |
| GET | `/api/students/{name}/report` | Bearer | Get JSON report |
| POST | `/api/students/{name}/report/pdf` | Bearer | Download PDF report |
| GET | `/api/export` | Bearer | Export all data as JSON |
| POST | `/api/import?mode=replace\|merge` | Bearer | Import data from JSON |
| POST | `/api/reset-admin` | No | Reset admin with master password |
| POST | `/api/logout` | No | Clear auth cookie |

## Project Structure

```
student_tracker/
├── app/
│   ├── main.py            # FastAPI app, routes, auth, command handler
│   ├── models.py           # SQLAlchemy models + migrations
│   ├── config.py           # Settings (DB path, secret key, etc.)
│   ├── commands.py         # Slash command parser
│   └── pdf_generator.py    # PDF report generation with CSS visuals
├── static/
│   ├── index.html          # Chat UI + login/setup modals
│   ├── dashboard.html      # Student detail dashboard
│   ├── students.html        # Student list page
│   └── setup.html           # First-time admin setup
├── tests/
│   ├── test_commands.py     # Command parsing tests
│   ├── test_api.py          # API endpoint tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_lockout.py      # Login lockout tests
│   ├── test_master_password.py  # Master password reset tests
│   ├── test_pdf.py          # PDF generation tests
│   └── test_frontend.py     # Jinja2 template tests
├── data/                    # Persistent database (created at runtime)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── ARCHITECTURE.md
└── AGENTS.md
```

## Running Tests

```bash
pytest                          # Run all tests
pytest tests/test_commands.py  # Command parser only
pytest tests/test_api.py       # API endpoints only
pytest -k test_progress       # Run tests matching pattern
pytest -v                      # Verbose output
```

## Configuration

Environment variables (set in `.env` or `docker-compose.yml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Student Tracker | Application title |
| `DB_PATH` | student_tracker.db | SQLite database path |
| `SECRET_KEY` | dev-secret-key-change-in-production | JWT signing key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token expiry time |
| `MASTER_PASSWORD` | RESET-admin-2024 | Password for account reset |

## License

MIT