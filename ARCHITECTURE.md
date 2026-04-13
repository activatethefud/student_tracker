# Student Tracker Architecture

## File Dependency Chain

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           STATIC FILES                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  index.html (main chat UI)                                             │
│    ├── Uses: localStorage for authToken                                │
│    └── Links: /students (Dashboard button)                              │
│                                                                         │
│  dashboard.html (student detail page)                                    │
│    ├── Uses: /api/grades/{id} (PUT/DELETE)                             │
│    ├── Uses: /api/behaviors/{id} (PUT/DELETE)                          │
│    ├── Uses: /api/attendance/{id} (PUT/DELETE)                         │
│    ├── Uses: /api/homework/{id} (PUT/DELETE)                           │
│    ├── Uses: /api/students/{name} (PUT/DELETE)                         │
│    └── Uses: localStorage for authToken                                 │
│                                                                         │
│  students.html (list all students)                                     │
│    └── Links: /student/{name}                                          │
│                                                                         │
│  setup.html (admin account creation)                                    │
│    └── Uses: /api/init-admin                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (app/main.py)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ROUTES (dependencies in order):                                        │
│                                                                         │
│  1. GET /  (no auth)                                                    │
│     └── Renders: index.html                                             │
│     └── Uses: commands.parse_command() for /help                      │
│                                                                         │
│  2. GET /setup (no auth)                                                │
│     └── Renders: setup.html                                             │
│                                                                         │
│  3. POST /token (login)                                                 │
│     └── Returns: JWT token (no auth needed for login)                   │
│                                                                         │
│  4. POST /api/command (auth required)                                  │
│     └── Uses: commands.parse_command() → determines action              │
│     └── Actions: add_student, add_grade, add_behavior,                  │
│                  add_attendance, add_homework, get_report,             │
│                  open_dashboard, list_dashboard                        │
│                                                                         │
│  5. API Endpoints (auth required):                                      │
│     ├── POST   /api/students        → create student                   │
│     ├── GET    /api/students        → list students (JSON)             │
│     ├── POST   /api/grades          → add grade                        │
│     ├── POST   /api/behaviors       → add behavior                     │
│     ├── POST   /api/attendance      → add attendance                   │
│     ├── GET    /api/students/{name}/report → get report (JSON)         │
│     ├── POST   /api/students/{name}/report/pdf → get PDF               │
│     ├── PUT    /api/grades/{id}     → update grade                    │
│     ├── DELETE /api/grades/{id}     → delete grade                    │
│     ├── PUT    /api/behaviors/{id}  → update behavior                  │
│     ├── DELETE /api/behaviors/{id}  → delete behavior                  │
│     ├── PUT    /api/attendance/{id} → update attendance               │
│     ├── DELETE /api/attendance/{id} → delete attendance                │
│     ├── PUT    /api/homework/{id}   → update homework                  │
│     ├── DELETE /api/homework/{id}   → delete homework                  │
│     ├── PUT    /api/students/{name} → update student                   │
│     ├── DELETE /api/students/{name} → delete student (cascade)         │
│     ├── POST   /api/init-admin      → create first admin               │
│     └── POST   /api/reset-admin     → reset admin with master password │
│                                                                         │
│  6. Page Routes (no auth):                                              │
│     ├── GET /students      → renders students.html                      │
│     └── GET /student/{name} → renders dashboard.html                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMMANDS (app/commands.py)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  parse_command(input_string) → dict                                     │
│                                                                         │
│  Commands handled:                                                       │
│  ├── /add-student <name> [--details "..."]                             │
│  ├── /grade <name> <score> [--subject <sub>] [--date YYYY-MM-DD]      │
│  ├── /behavior <name> <type> [--note "..."] [--date YYYY-MM-DD]        │
│  ├── /attendance <name> <status> [--date YYYY-MM-DD]                   │
│  ├── /homework <name> <title> [--due YYYY-MM-DD] [--status <status>]   │
│  ├── /report <name> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--pdf]      │
│  ├── /dashboard [<name>] / /dash / /d                                   │
│  └── /help                                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          MODELS (app/models.py)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Database Schema (SQLAlchemy):                                          │
│                                                                         │
│  User (id, username, hashed_password, created_at)                      │
│      └── No relationships                                               │
│                                                                         │
│  Student (id, name, details, created_at)                                │
│       ├── grades: List[Grade] (cascade delete)                          │
│       ├── behaviors: List[Behavior] (cascade delete)                   │
│       ├── attendances: List[Attendance] (cascade delete)               │
│       └── homeworks: List[Homework] (cascade delete)                   │
│                                                                         │
│  Grade (id, student_id, score, subject, created_at)                    │
│       └── student: Student (relationship)                               │
│                                                                         │
│  Behavior (id, student_id, note, behavior_type, created_at)            │
│       └── student: Student (relationship)                               │
│                                                                         │
│  Attendance (id, student_id, status, date)                               │
│       └── student: Student (relationship)                               │
│                                                                         │
│  Homework (id, student_id, title, due_date, status, created_at)         │
│       └── student: Student (relationship)                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    PDF GENERATOR (app/pdf_generator.py)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  generate_pdf_report(student, grades, behaviors, attendances,         │
│                       homeworks, avg_grade, date_range)                │
│     └── Uses: weasyprint to convert HTML to PDF                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CONFIG (app/config.py)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Settings:                                                              │
│  ├── app_name = "Student Tracker"                                      │
│  ├── db_path = "students.db"                                           │
│  ├── secret_key = "student-tracker-secret-key"                         │
│  └── algorithm = "HS256"                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           TESTS                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  test_commands.py    → Tests for parse_command()                       │
│  test_api.py         → Tests for API endpoints (auth required)        │
│  test_frontend.py    → Tests for Jinja2 templates                      │
│  test_auth.py        → Tests for authentication                        │
│  test_lockout.py     → Tests for login lockout                          │
│  test_master_password.py → Tests for master password reset            │
│  test_pdf.py         → Tests for PDF generation                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## When Adding New Features

### 1. New Command (slash command in chat)
- Update: `app/commands.py` - add parsing in `parse_command()`
- Update: `app/main.py` - add handler in `execute_command()`
- Update: `static/index.html` - add example in help message
- Update: `tests/test_commands.py` - add test cases

### 2. New API Endpoint
- Update: `app/main.py` - add route with appropriate auth
- Update: `tests/test_api.py` - add test cases

### 3. New Page/Template
- Create: `static/new_page.html`
- Update: `app/main.py` - add GET route (decide if auth needed)
- Update: `tests/test_frontend.py` - add template tests

### 4. New Data Model
- Update: `app/models.py` - add SQLAlchemy model
- Update: `app/main.py` - add CRUD endpoints if needed
- Update: `app/pdf_generator.py` - include in PDF if relevant
- Update: `tests/test_api.py` - add model tests

### 5. Frontend UI Changes
- Update: `static/index.html` or other template
- Update: `tests/test_frontend.py` - verify template compiles

### 6. After Any Change
1. Run tests: `pytest`
2. Commit with conventional message
3. Push to remote: `git push origin main`