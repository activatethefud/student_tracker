from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    behaviors = relationship("Behavior", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")


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