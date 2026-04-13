import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db, failed_login_attempts
from app.models import Base, Student, User, Grade, Behavior, Attendance, Homework, Activity
import bcrypt


TEST_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    failed_login_attempts.clear()
    Base.metadata.create_all(bind=engine)
    yield
    failed_login_attempts.clear()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.query(Student).delete()
    db.commit()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def admin_user(db):
    hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    user = User(username="admin", hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_with_data(db, admin_user):
    s = Student(name="John", details="Good student")
    db.add(s)
    db.commit()
    db.refresh(s)
    
    g1 = Grade(student_id=s.id, score=85, subject="Math")
    g2 = Grade(student_id=s.id, score=90, subject="Science")
    db.add_all([g1, g2])
    
    b1 = Behavior(student_id=s.id, note="Helped peer", behavior_type="positive")
    db.add(b1)
    
    a1 = Attendance(student_id=s.id, status="present")
    db.add(a1)
    
    db.commit()
    return s


@pytest.fixture
def student_with_full_data(db, admin_user):
    s = Student(name="Jane", student_id="STU-100", year="Grade 8", details="Excellent student")
    db.add(s)
    db.commit()
    db.refresh(s)
    
    g1 = Grade(student_id=s.id, score=92, subject="Math")
    g2 = Grade(student_id=s.id, score=88, subject="Science")
    g3 = Grade(student_id=s.id, score=75, subject="English")
    db.add_all([g1, g2, g3])
    
    b1 = Behavior(student_id=s.id, note="Helped peer", behavior_type="positive")
    b2 = Behavior(student_id=s.id, note="Disruptive", behavior_type="negative")
    db.add_all([b1, b2])
    
    a1 = Attendance(student_id=s.id, status="present")
    a2 = Attendance(student_id=s.id, status="absent")
    a3 = Attendance(student_id=s.id, status="late")
    db.add_all([a1, a2, a3])
    
    h1 = Homework(student_id=s.id, title="Chapter 5", status="submitted")
    h2 = Homework(student_id=s.id, title="Essay", status="pending")
    db.add_all([h1, h2])
    
    act1 = Activity(student_id=s.id, activity_type="taking-notes", status="yes")
    act2 = Activity(student_id=s.id, activity_type="taking-notes", status="no")
    act3 = Activity(student_id=s.id, activity_type="participation", status="yes")
    db.add_all([act1, act2, act3])
    
    db.commit()
    return s


class TestPDFGeneration:
    def test_pdf_endpoint_returns_pdf(self, client, admin_user, student_with_data):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/students/John/report/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
    
    def test_pdf_endpoint_with_date_filter(self, client, admin_user, student_with_data):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/students/John/report/pdf?date_from=2025-01-01&date_to=2025-12-31",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_pdf_command_returns_pdf(self, client, admin_user, student_with_data):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/report John --pdf"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_pdf_endpoint_student_not_found(self, client, admin_user):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/students/Nonexistent/report/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is False
    
    def test_pdf_with_full_data(self, client, admin_user, student_with_full_data):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/students/Jane/report/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        pdf_content = response.content
        assert len(pdf_content) > 100
    
    def test_pdf_with_activities(self, client, admin_user, student_with_data, db):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        act = Activity(student_id=student_with_data.id, activity_type="focus", status="yes")
        db.add(act)
        db.commit()
        
        response = client.post(
            "/api/students/John/report/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_pdf_with_empty_student(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login.json()["access_token"]
        
        s = Student(name="EmptyStudent")
        db.add(s)
        db.commit()
        
        response = client.post(
            "/api/students/EmptyStudent/report/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"