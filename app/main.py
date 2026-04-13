from datetime import datetime, timedelta, date
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.models import Base, get_engine, get_session, Student, Grade, Behavior, Attendance, Homework, User, generate_student_id, assign_missing_student_ids
from app.config import settings
from app.commands import parse_command

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory="static")
app.mount("/static", StaticFiles(directory="static"), name="static")

engine = get_engine(settings.db_path)

failed_login_attempts = {}


def resolve_student(db: Session, identifier: str):
    """
    Resolve a student by name or student_id (supports prefix matching).
    Returns (student, error_message) where error_message is None on success.
    """
    identifier = identifier.strip()
    
    # First try exact student_id match
    student = db.query(Student).filter(Student.student_id == identifier).first()
    if student:
        return student, None
    
    # Try prefix match on student_id
    students = db.query(Student).filter(Student.student_id.like(f"{identifier}%")).all()
    if len(students) == 1:
        return students[0], None
    if len(students) > 1:
        return None, f"Multiple students match '{identifier}': " + ", ".join(
            f"{s.name} ({s.student_id}, {s.year})" for s in students
        ) + ". Use student ID (e.g., /report STU-001)"
    
    # Try exact name match
    student = db.query(Student).filter(Student.name == identifier).first()
    if student:
        return student, None
    
    # Try partial name match
    students = db.query(Student).filter(Student.name.ilike(f"%{identifier}%")).all()
    if len(students) == 1:
        return students[0], None
    if len(students) > 1:
        return None, f"Multiple students match '{identifier}': " + ", ".join(
            f"{s.name} ({s.student_id}, {s.year})" for s in students
        ) + ". Use student ID (e.g., /report STU-001)"
    
    return None, f"Student '{identifier}' not found"


def get_db():
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


class StudentCreate(BaseModel):
    name: str
    details: Optional[str] = None


class GradeCreate(BaseModel):
    student_name: str
    score: float
    subject: str = "General"


class BehaviorCreate(BaseModel):
    student_name: str
    note: str
    behavior_type: str = "neutral"


class AttendanceCreate(BaseModel):
    student_name: str
    status: str


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    db = get_session(engine)
    try:
        # Add new columns if they don't exist (for existing databases)
        from sqlalchemy import text
        try:
            result = db.execute(text("PRAGMA table_info(students)"))
            columns = [row[1] for row in result.fetchall()]
            if 'student_id' not in columns:
                db.execute(text("ALTER TABLE students ADD COLUMN student_id VARCHAR(20)"))
            if 'year' not in columns:
                db.execute(text("ALTER TABLE students ADD COLUMN year VARCHAR(50)"))
            db.commit()
        except Exception as e:
            db.rollback()
        
        # Try to assign IDs - will fail gracefully if columns don't exist
        try:
            assign_missing_student_ids(db)
        except Exception:
            pass  # Skip if columns don't exist yet
    finally:
        db.close()


@app.get("/")
def home(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    admin_exists = db.query(User).first() is not None
    return templates.TemplateResponse("index.html", {"request": {}, "students": students, "admin_exists": admin_exists})


@app.get("/setup")
def setup_page(db: Session = Depends(get_db)):
    admin_exists = db.query(User).first() is not None
    if admin_exists:
        return RedirectResponse("/")
    return templates.TemplateResponse("setup.html", {"request": {}})


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    password = form_data.password
    
    if username in failed_login_attempts and failed_login_attempts[username]["count"] >= 3:
        if not password:
            raise HTTPException(status_code=423, detail="Account locked. Use master password to reset.")
        
        if password == settings.master_password:
            db.query(User).delete()
            db.commit()
            new_admin = User(username="admin", hashed_password=get_password_hash("admin123"))
            db.add(new_admin)
            db.commit()
            failed_login_attempts.pop(username, None)
            return {"access_token": create_access_token(data={"sub": "admin"}), "token_type": "bearer", "message": "Admin reset to default (admin/admin123). Master password worked!"}
        
        failed_login_attempts[username]["count"] += 1
        remaining = 3 - failed_login_attempts[username]["count"]
        if remaining > 0:
            raise HTTPException(status_code=423, detail=f"Account locked. {remaining} attempts left. Use master password to reset.")
        else:
            raise HTTPException(status_code=423, detail="Account locked. Use master password to reset.")
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        if username not in failed_login_attempts:
            failed_login_attempts[username] = {"count": 1, "time": datetime.utcnow()}
        else:
            failed_login_attempts[username]["count"] += 1
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    failed_login_attempts.pop(username, None)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/students")
def add_student(student: StudentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Student).filter(Student.name == student.name).first()
    if existing:
        return {"success": False, "message": f"Student '{student.name}' already exists"}
    new_student = Student(name=student.name, details=student.details)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"success": True, "message": f"Added student: {student.name}", "student": {"id": new_student.id, "name": new_student.name}}


@app.get("/api/students")
def list_students(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    students = db.query(Student).all()
    return [{"id": s.id, "name": s.name, "student_id": s.student_id, "year": s.year, "details": s.details} for s in students]


@app.post("/api/grades")
def add_grade(grade: GradeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.name == grade.student_name).first()
    if not student:
        return {"success": False, "message": f"Student '{grade.student_name}' not found. Use /add-student first."}
    new_grade = Grade(student_id=student.id, score=grade.score, subject=grade.subject)
    db.add(new_grade)
    db.commit()
    return {"success": True, "message": f"Added {grade.subject} grade {grade.score} for {grade.student_name}"}


@app.post("/api/behaviors")
def add_behavior(behavior: BehaviorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.name == behavior.student_name).first()
    if not student:
        return {"success": False, "message": f"Student '{behavior.student_name}' not found. Use /add-student first."}
    new_behavior = Behavior(student_id=student.id, note=behavior.note, behavior_type=behavior.behavior_type)
    db.add(new_behavior)
    db.commit()
    return {"success": True, "message": f"Recorded {behavior.behavior_type} behavior for {behavior.student_name}: {behavior.note}"}


@app.post("/api/attendance")
def mark_attendance(attendance: AttendanceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.name == attendance.student_name).first()
    if not student:
        return {"success": False, "message": f"Student '{attendance.student_name}' not found. Use /add-student first."}
    new_attendance = Attendance(student_id=student.id, status=attendance.status)
    db.add(new_attendance)
    db.commit()
    return {"success": True, "message": f"Marked {attendance.student_name} as {attendance.status}"}


@app.get("/api/students/{student_name}/report")
def get_student_report(student_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        return {"success": False, "message": f"Student '{student_name}' not found"}
    
    grades = [{"score": g.score, "subject": g.subject, "date": g.created_at.isoformat()} for g in student.grades]
    behaviors = [{"note": b.note, "type": b.behavior_type, "date": b.created_at.isoformat()} for b in student.behaviors]
    attendances = [{"status": a.status, "date": a.date.isoformat()} for a in student.attendances]
    
    avg_grade = sum(g["score"] for g in grades) / len(grades) if grades else 0
    
    return {
        "success": True,
        "student": {"name": student.name, "details": student.details},
        "grades": grades,
        "behaviors": behaviors,
        "attendance": attendances,
        "average_grade": round(avg_grade, 2)
    }


@app.get("/students")
def list_students_page(db: Session = Depends(get_db)):
    students = db.query(Student).order_by(Student.name).all()
    return templates.TemplateResponse("students.html", {"request": {}, "students": students})


@app.get("/student/{student_name}")
def student_dashboard(student_name: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_name}' not found")
    
    grades = student.grades
    behaviors = student.behaviors
    attendances = student.attendances
    homeworks = student.homeworks
    
    avg_grade = sum(g.score for g in grades) / len(grades) if grades else 0
    present = len([a for a in attendances if a.status == "present"])
    total = len(attendances)
    attendance_pct = round((present / total) * 100, 1) if total > 0 else 0
    
    pending_hw = len([h for h in homeworks if h.status.lower() == "pending"])
    submitted_hw = len([h for h in homeworks if h.status.lower() == "submitted"])
    other_hw = len(homeworks) - pending_hw - submitted_hw
    
    return templates.TemplateResponse("dashboard.html", {
        "request": {},
        "student": student,
        "grades": grades,
        "behaviors": behaviors,
        "attendances": attendances,
        "homeworks": homeworks,
        "avg_grade": round(avg_grade, 2),
        "attendance_pct": attendance_pct,
        "pending_hw": pending_hw,
        "submitted_hw": submitted_hw,
        "other_hw": other_hw
    })


class GradeUpdate(BaseModel):
    score: Optional[float] = None
    subject: Optional[str] = None


@app.put("/api/grades/{grade_id}")
def update_grade(grade_id: int, update: GradeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    if update.score is not None:
        grade.score = update.score
    if update.subject is not None:
        grade.subject = update.subject
    
    db.commit()
    return {"success": True, "message": f"Updated grade {grade_id}"}


@app.delete("/api/grades/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    db.delete(grade)
    db.commit()
    return {"success": True, "message": f"Deleted grade {grade_id}"}


class BehaviorUpdate(BaseModel):
    note: Optional[str] = None
    behavior_type: Optional[str] = None


@app.put("/api/behaviors/{behavior_id}")
def update_behavior(behavior_id: int, update: BehaviorUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    behavior = db.query(Behavior).filter(Behavior.id == behavior_id).first()
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    
    if update.note is not None:
        behavior.note = update.note
    if update.behavior_type is not None:
        behavior.behavior_type = update.behavior_type
    
    db.commit()
    return {"success": True, "message": f"Updated behavior {behavior_id}"}


@app.delete("/api/behaviors/{behavior_id}")
def delete_behavior(behavior_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    behavior = db.query(Behavior).filter(Behavior.id == behavior_id).first()
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    
    db.delete(behavior)
    db.commit()
    return {"success": True, "message": f"Deleted behavior {behavior_id}"}


class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    date: Optional[str] = None


@app.put("/api/attendance/{attendance_id}")
def update_attendance(attendance_id: int, update: AttendanceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    
    if update.status is not None:
        attendance.status = update.status
    if update.date is not None:
        attendance.date = datetime.strptime(update.date, "%Y-%m-%d").date()
    
    db.commit()
    return {"success": True, "message": f"Updated attendance {attendance_id}"}


@app.delete("/api/attendance/{attendance_id}")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    
    db.delete(attendance)
    db.commit()
    return {"success": True, "message": f"Deleted attendance {attendance_id}"}


class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None


@app.put("/api/homework/{homework_id}")
def update_homework(homework_id: int, update: HomeworkUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    if update.title is not None:
        homework.title = update.title
    if update.status is not None:
        homework.status = update.status
    if update.due_date is not None:
        homework.due_date = datetime.strptime(update.due_date, "%Y-%m-%d").date()
    
    db.commit()
    return {"success": True, "message": f"Updated homework {homework_id}"}


@app.delete("/api/homework/{homework_id}")
def delete_homework(homework_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    db.delete(homework)
    db.commit()
    return {"success": True, "message": f"Deleted homework {homework_id}"}


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[str] = None
    details: Optional[str] = None


@app.put("/api/students/{student_name}")
def update_student(student_name: str, update: StudentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Try to resolve by name or student_id (handles renamed students too)
    student, error = resolve_student(db, student_name)
    if error:
        raise HTTPException(status_code=404, detail=error)
    
    if update.name is not None:
        student.name = update.name
    if update.year is not None:
        student.year = update.year
    if update.details is not None:
        student.details = update.details
    
    db.commit()
    return {"success": True, "message": f"Updated student {student_name}"}


@app.delete("/api/students/{student_name}")
def delete_student(student_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    return {"success": True, "message": f"Deleted student {student_name} and all related records"}


@app.post("/api/setup-admin")
def setup_admin(username: str = "admin", password: str = "admin", db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return {"success": False, "message": "Admin user already exists"}
    admin = User(username=username, hashed_password=get_password_hash(password))
    db.add(admin)
    db.commit()
    return {"success": True, "message": f"Admin user created. Username: {username}, Password: {password}"}


class CommandRequest(BaseModel):
    command: str


@app.post("/api/command")
def execute_command(request: CommandRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cmd = parse_command(request.command)
    
    if cmd["action"] == "help":
        return {"success": True, "message": cmd["message"]}
    
    if cmd["action"] == "invalid" or cmd["action"] == "error":
        return {"success": False, "message": cmd["message"]}
    
    if cmd["action"] == "add_student":
        existing = db.query(Student).filter(Student.name == cmd["name"]).first()
        if existing:
            return {"success": False, "message": f"Student '{cmd['name']}' already exists"}
        new_student = Student(
            name=cmd["name"],
            year=cmd.get("year"),
            details=cmd.get("details"),
            student_id=generate_student_id(db)
        )
        db.add(new_student)
        db.commit()
        year_msg = f" (Year: {cmd['year']})" if cmd.get("year") else ""
        return {"success": True, "message": f"Added student: {cmd['name']} (ID: {new_student.student_id}){year_msg}"}
    
    if cmd["action"] == "add_grade":
        student, error = resolve_student(db, cmd["student_name"])
        if error:
            return {"success": False, "message": error}
        new_grade = Grade(student_id=student.id, score=cmd["score"], subject=cmd["subject"])
        if cmd.get("date"):
            try:
                new_grade.created_at = datetime.strptime(cmd["date"], "%Y-%m-%d")
            except ValueError:
                pass
        db.add(new_grade)
        db.commit()
        date_msg = f" (dated: {cmd['date']})" if cmd.get("date") else ""
        return {"success": True, "message": f"Added {cmd['subject']} grade {cmd['score']} for {cmd['student_name']}{date_msg}"}
    
    if cmd["action"] == "add_behavior":
        student, error = resolve_student(db, cmd["student_name"])
        if error:
            return {"success": False, "message": error}
        new_behavior = Behavior(student_id=student.id, note=cmd["note"], behavior_type=cmd["behavior_type"])
        if cmd.get("date"):
            try:
                new_behavior.created_at = datetime.strptime(cmd["date"], "%Y-%m-%d")
            except ValueError:
                pass
        db.add(new_behavior)
        db.commit()
        date_msg = f" (dated: {cmd['date']})" if cmd.get("date") else ""
        return {"success": True, "message": f"Recorded {cmd['behavior_type']} behavior for {cmd['student_name']}: {cmd['note']}{date_msg}"}
    
    if cmd["action"] == "mark_attendance":
        student, error = resolve_student(db, cmd["student_name"])
        if error:
            return {"success": False, "message": error}
        if cmd["status"] not in ("present", "absent", "late"):
            return {"success": False, "message": "Status must be: present, absent, or late"}
        new_attendance = Attendance(student_id=student.id, status=cmd["status"])
        if cmd.get("date"):
            try:
                new_attendance.date = datetime.strptime(cmd["date"], "%Y-%m-%d")
            except ValueError:
                pass
        db.add(new_attendance)
        db.commit()
        date_msg = f" (dated: {cmd['date']})" if cmd.get("date") else ""
        return {"success": True, "message": f"Marked {cmd['student_name']} as {cmd['status']}{date_msg}"}
    
    if cmd["action"] == "add_homework":
        student, error = resolve_student(db, cmd["student_name"])
        if error:
            return {"success": False, "message": error}
        new_homework = Homework(student_id=student.id, title=cmd["title"], status=cmd["status"])
        if cmd.get("due_date"):
            try:
                new_homework.due_date = datetime.strptime(cmd["due_date"], "%Y-%m-%d")
            except ValueError:
                pass
        db.add(new_homework)
        db.commit()
        due_msg = f", due: {cmd['due_date']}" if cmd.get("due_date") else ""
        return {"success": True, "message": f"Added homework for {cmd['student_name']}: {cmd['title']} (status: {cmd['status']}){due_msg}"}
    
    if cmd["action"] == "get_report":
        student, error = resolve_student(db, cmd["student_name"])
        if error:
            return {"success": False, "message": error}
        
        grades = student.grades
        behaviors = student.behaviors
        attendances = student.attendances
        homeworks = student.homeworks
        
        date_from = cmd.get("date_from")
        date_to = cmd.get("date_to")
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                grades = [g for g in grades if g.created_at >= from_date]
                behaviors = [b for b in behaviors if b.created_at >= from_date]
                attendances = [a for a in attendances if a.date >= from_date]
                homeworks = [h for h in homeworks if h.created_at >= from_date]
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                to_date = to_date + timedelta(days=1)
                grades = [g for g in grades if g.created_at < to_date]
                behaviors = [b for b in behaviors if b.created_at < to_date]
                attendances = [a for a in attendances if a.date < to_date]
                homeworks = [h for h in homeworks if h.created_at < to_date]
            except ValueError:
                pass
        
        avg_grade = sum(g.score for g in grades) / len(grades) if grades else 0
        
        date_range = ""
        if date_from and date_to:
            date_range = f" ({date_from} to {date_to})"
        elif date_from:
            date_range = f" (from {date_from})"
        elif date_to:
            date_range = f" (to {date_to})"
        
        student_info = f"{student.name}"
        if student.student_id:
            student_info += f" (ID: {student.student_id})"
        if student.year:
            student_info += f" - {student.year}"
        
        report = f"<strong>Report for {student_info}</strong>{date_range}\n"
        report += f"Average Grade: {avg_grade:.2f}\n"
        report += f"Grades: {', '.join(f'{g.score} ({g.subject})' for g in grades) or 'None'}\n"
        report += f"Behaviors: {', '.join(f'{b.behavior_type}' for b in behaviors) or 'None'}\n"
        report += f"Attendance: {len([a for a in attendances if a.status == 'present'])}/present, {len([a for a in attendances if a.status == 'absent'])}/absent\n"
        report += f"Homework: {len([h for h in homeworks if h.status.lower() == 'pending'])} pending, {len([h for h in homeworks if h.status.lower() == 'submitted'])} submitted, {len([h for h in homeworks if h.status.lower() not in ['pending', 'submitted']])} other"
        
        if cmd.get("pdf"):
            from app.pdf_generator import generate_pdf_report
            date_range_display = date_range.replace("(", "").replace(")", "") if date_range else ""
            pdf_content = generate_pdf_report(student, grades, behaviors, attendances, homeworks, avg_grade, date_range_display)
            return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{student.name}.pdf"})
        
        return {"success": True, "message": report}
    
    if cmd["action"] == "open_dashboard":
        student, error = resolve_student(db, cmd["student_name"])
        if error:
            return {"success": False, "message": error}
        return {"success": True, "action": "redirect", "url": f"/student/{student.name}"}
    
    if cmd["action"] == "list_dashboard":
        return {"success": True, "action": "redirect", "url": "/students"}


@app.post("/api/init-admin")
def init_admin(username: str = "admin", password: str = "admin123", db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return {"success": False, "message": f"User '{username}' already exists"}
    admin = User(username=username, hashed_password=get_password_hash(password))
    db.add(admin)
    db.commit()
    return {"success": True, "message": f"Admin created. Username: {username}, Password: {password}"}


@app.post("/api/students/{student_name}/report/pdf")
def generate_pdf(student_name: str, date_from: str = None, date_to: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.pdf_generator import generate_pdf_report
    
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        return {"success": False, "message": f"Student '{student_name}' not found"}
    
    grades = student.grades
    behaviors = student.behaviors
    attendances = student.attendances
    homeworks = student.homeworks
    
    if date_from:
        from_date = datetime.strptime(date_from, "%Y-%m-%d")
        grades = [g for g in grades if g.created_at >= from_date]
        behaviors = [b for b in behaviors if b.created_at >= from_date]
        attendances = [a for a in attendances if a.date >= from_date]
        homeworks = [h for h in homeworks if h.created_at >= from_date]
    
    if date_to:
        to_date = datetime.strptime(date_to, "%Y-%m-%d")
        to_date = to_date + timedelta(days=1)
        grades = [g for g in grades if g.created_at < to_date]
        behaviors = [b for b in behaviors if b.created_at < to_date]
        attendances = [a for a in attendances if a.date < to_date]
        homeworks = [h for h in homeworks if h.created_at < to_date]
    
    avg_grade = sum(g.score for g in grades) / len(grades) if grades else 0
    
    date_range = ""
    if date_from and date_to:
        date_range = f"{date_from} to {date_to}"
    elif date_from:
        date_range = f"from {date_from}"
    elif date_to:
        date_range = f"to {date_to}"
    
    pdf_content = generate_pdf_report(student, grades, behaviors, attendances, homeworks, avg_grade, date_range)
    
    return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{student_name}.pdf"})


@app.post("/api/reset-admin")
def reset_admin(username: str = "admin", password: str = "admin123", master_password: str = "", db: Session = Depends(get_db)):
    if master_password != settings.master_password:
        return {"success": False, "message": "Invalid master password"}
    
    db.query(User).delete()
    db.commit()
    
    admin = User(username=username, hashed_password=get_password_hash(password))
    db.add(admin)
    db.commit()
    return {"success": True, "message": f"Admin reset. Username: {username}, Password: {password}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)