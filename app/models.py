from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), unique=True, nullable=True)  # e.g., "STU-001"
    name = Column(String(200), nullable=False)
    year = Column(String(50), nullable=True)  # e.g., "Grade 8", "Grade 1"
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    behaviors = relationship("Behavior", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    homeworks = relationship("Homework", back_populates="student", cascade="all, delete-orphan")


def generate_student_id(session):
    """Generate unique student ID like STU-001, STU-002, etc."""
    last_student = session.query(Student).filter(Student.student_id != None).order_by(Student.id.desc()).first()
    if last_student and last_student.student_id:
        try:
            num = int(last_student.student_id.split("-")[1])
            return f"STU-{num + 1:03d}"
        except:
            pass
    return "STU-001"


def assign_missing_student_ids(session):
    """Assign student IDs to students who don't have one."""
    students_without_id = session.query(Student).filter(Student.student_id == None).order_by(Student.id).all()
    for student in students_without_id:
        student.student_id = generate_student_id(session)
    if students_without_id:
        session.commit()


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float, nullable=False)
    subject = Column(String(100), default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="grades")


class Behavior(Base):
    __tablename__ = "behaviors"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    note = Column(Text, nullable=False)
    behavior_type = Column(String(20), default="neutral")  # positive, negative, neutral
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="behaviors")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(String(20), nullable=False)  # present, absent, late
    date = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="attendances")


class Homework(Base):
    __tablename__ = "homeworks"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(200), nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # pending, submitted
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="homeworks")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine(db_path="student_tracker.db"):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(engine):
    Base.metadata.create_all(engine)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()