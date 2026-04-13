from datetime import datetime, timedelta, date
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.models import Base, get_engine, get_session, Student, Grade, Behavior, Attendance, User
from app.config import settings
from app.commands import parse_command

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory="static")
app.mount("/static", StaticFiles(directory="static"), name="static")

engine = get_engine(settings.db_path)


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


@app.get("/")
def home(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return templates.TemplateResponse("index.html", {"request": {}, "students": students})


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
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
    return [{"id": s.id, "name": s.name, "details": s.details} for s in students]


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
def execute_command(request: CommandRequest, db: Session = Depends(get_db)):
    cmd = parse_command(request.command)
    
    if cmd["action"] == "help":
        return {"success": True, "message": cmd["message"]}
    
    if cmd["action"] == "invalid" or cmd["action"] == "error":
        return {"success": False, "message": cmd["message"]}
    
    if cmd["action"] == "add_student":
        existing = db.query(Student).filter(Student.name == cmd["name"]).first()
        if existing:
            return {"success": False, "message": f"Student '{cmd['name']}' already exists"}
        new_student = Student(name=cmd["name"], details=cmd.get("details"))
        db.add(new_student)
        db.commit()
        return {"success": True, "message": f"Added student: {cmd['name']}"}
    
    if cmd["action"] == "add_grade":
        student = db.query(Student).filter(Student.name == cmd["student_name"]).first()
        if not student:
            return {"success": False, "message": f"Student '{cmd['student_name']}' not found. Use /add-student first."}
        new_grade = Grade(student_id=student.id, score=cmd["score"], subject=cmd["subject"])
        db.add(new_grade)
        db.commit()
        return {"success": True, "message": f"Added {cmd['subject']} grade {cmd['score']} for {cmd['student_name']}"}
    
    if cmd["action"] == "add_behavior":
        student = db.query(Student).filter(Student.name == cmd["student_name"]).first()
        if not student:
            return {"success": False, "message": f"Student '{cmd['student_name']}' not found. Use /add-student first."}
        new_behavior = Behavior(student_id=student.id, note=cmd["note"], behavior_type=cmd["behavior_type"])
        db.add(new_behavior)
        db.commit()
        return {"success": True, "message": f"Recorded {cmd['behavior_type']} behavior for {cmd['student_name']}: {cmd['note']}"}
    
    if cmd["action"] == "mark_attendance":
        student = db.query(Student).filter(Student.name == cmd["student_name"]).first()
        if not student:
            return {"success": False, "message": f"Student '{cmd['student_name']}' not found. Use /add-student first."}
        if cmd["status"] not in ("present", "absent", "late"):
            return {"success": False, "message": "Status must be: present, absent, or late"}
        new_attendance = Attendance(student_id=student.id, status=cmd["status"])
        db.add(new_attendance)
        db.commit()
        return {"success": True, "message": f"Marked {cmd['student_name']} as {cmd['status']}"}
    
    if cmd["action"] == "get_report":
        student = db.query(Student).filter(Student.name == cmd["student_name"]).first()
        if not student:
            return {"success": False, "message": f"Student '{cmd['student_name']}' not found"}
        
        grades = student.grades
        behaviors = student.behaviors
        attendances = student.attendances
        
        date_from = cmd.get("date_from")
        date_to = cmd.get("date_to")
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                grades = [g for g in grades if g.created_at >= from_date]
                behaviors = [b for b in behaviors if b.created_at >= from_date]
                attendances = [a for a in attendances if a.date >= from_date]
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                to_date = to_date + timedelta(days=1)
                grades = [g for g in grades if g.created_at < to_date]
                behaviors = [b for b in behaviors if b.created_at < to_date]
                attendances = [a for a in attendances if a.date < to_date]
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
        
        report = f"<strong>Report for {student.name}</strong>{date_range}\n"
        report += f"Average Grade: {avg_grade:.2f}\n"
        report += f"Grades: {', '.join(f'{g.score} ({g.subject})' for g in grades) or 'None'}\n"
        report += f"Behaviors: {', '.join(f'{b.behavior_type}' for b in behaviors) or 'None'}\n"
        report += f"Attendance: {len([a for a in attendances if a.status == 'present'])}/present, {len([a for a in attendances if a.status == 'absent'])}/absent"
        
        if cmd.get("pdf"):
            from app.pdf_generator import generate_pdf_report
            date_range_display = date_range.replace("(", "").replace(")", "") if date_range else ""
            pdf_content = generate_pdf_report(student, grades, behaviors, attendances, avg_grade, date_range_display)
            return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{student.name}.pdf"})
        
        return {"success": True, "message": report}


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
    
    if date_from:
        from_date = datetime.strptime(date_from, "%Y-%m-%d")
        grades = [g for g in grades if g.created_at >= from_date]
        behaviors = [b for b in behaviors if b.created_at >= from_date]
        attendances = [a for a in attendances if a.date >= from_date]
    
    if date_to:
        to_date = datetime.strptime(date_to, "%Y-%m-%d")
        to_date = to_date + timedelta(days=1)
        grades = [g for g in grades if g.created_at < to_date]
        behaviors = [b for b in behaviors if b.created_at < to_date]
        attendances = [a for a in attendances if a.date < to_date]
    
    avg_grade = sum(g.score for g in grades) / len(grades) if grades else 0
    
    date_range = ""
    if date_from and date_to:
        date_range = f"{date_from} to {date_to}"
    elif date_from:
        date_range = f"from {date_from}"
    elif date_to:
        date_range = f"to {date_to}"
    
    pdf_content = generate_pdf_report(student, grades, behaviors, attendances, avg_grade, date_range)
    
    return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{student_name}.pdf"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)