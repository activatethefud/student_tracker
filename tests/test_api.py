import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db, failed_login_attempts
from app.models import Base, Student, User


TEST_DATABASE_URL = "sqlite:///./test.db"
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
    user = User(username="admin", hashed_password="$2b$12$1nnSGZ116q5KqAkgVZHSceZQ0NXzKMrGbKXC4fvbMLc5OkIIVWFZO")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student(db):
    s = Student(name="John")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


class TestSetupAdmin:
    def test_setup_admin(self, client):
        response = client.post("/api/init-admin?username=admin&password=pass")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "admin" in data["message"]


class TestStudentAPI:
    def test_add_student_unauthorized(self, client):
        response = client.post("/api/students", json={"name": "John"})
        assert response.status_code == 401

    def test_add_and_list_student(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/students",
            json={"name": "John"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["student"]["name"] == "John"
        
        list_response = client.get(
            "/api/students",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        students = list_response.json()
        assert len(students) == 1
        assert students[0]["name"] == "John"


class TestGradesAPI:
    def test_add_grade(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/grades",
            json={"student_name": "John", "score": 90, "subject": "Math"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "90" in data["message"]


class TestBehaviorAPI:
    def test_add_behavior(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/behaviors",
            json={"student_name": "John", "note": "Helped peer", "behavior_type": "positive"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAttendanceAPI:
    def test_mark_attendance(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/attendance",
            json={"student_name": "John", "status": "present"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestReportAPI:
    def test_get_report(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.get(
            "/api/students/John/report",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["student"]["name"] == "John"
        assert data["average_grade"] == 0


class TestCommandAPI:
    def test_add_student_command(self, client, admin_user):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/add-student Alice"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Alice" in data["message"]
    
    def test_grade_command(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/grade John 95 --subject Science"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "95" in data["message"]
    
    def test_behavior_command(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/behavior John positive --note \"Great work today\""},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_attendance_command(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/attendance John late"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "late" in data["message"]
    
    def test_report_command(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/report John"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "John" in data["message"]
    
    def test_help_command(self, client):
        response = client.post("/api/command", json={"command": "/help"})
        assert response.status_code == 401
    
    def test_unknown_command(self, client):
        response = client.post("/api/command", json={"command": "/unknown arg"})
        assert response.status_code == 401
    
    def test_command_student_not_found(self, client, admin_user):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/grade Nonexistent 100"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()


class TestInitAdmin:
    def test_init_admin_creates_user(self, client, db):
        response = client.post("/api/init-admin?username=teacher&password=teach123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "teacher" in data["message"]
    
    def test_init_admin_fails_if_exists(self, client, db, admin_user):
        response = client.post("/api/init-admin?username=admin&password=pass123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False