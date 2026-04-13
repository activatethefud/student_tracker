import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db, failed_login_attempts
from app.models import Base, Student, User, Grade, Behavior, Attendance
import bcrypt


TEST_DATABASE_URL = "sqlite:///./test_pdf.db"
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