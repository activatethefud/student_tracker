import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.models import Base, Student, User
import bcrypt


TEST_DATABASE_URL = "sqlite:///./test_auth.db"
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
    Base.metadata.create_all(bind=engine)
    yield
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
def second_user(db):
    hashed = bcrypt.hashpw(b"teacher456", bcrypt.gensalt()).decode()
    user = User(username="teacher", hashed_password=hashed)
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


@pytest.fixture
def auth_headers(client, admin_user):
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuthLogin:
    def test_login_success(self, client, admin_user):
        response = client.post("/token", data={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, admin_user):
        response = client.post("/token", data={"username": "admin", "password": "wrongpass"})
        assert response.status_code == 400
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        response = client.post("/token", data={"username": "nonexistent", "password": "pass"})
        assert response.status_code == 400
    
    def test_login_empty_username(self, client, admin_user):
        response = client.post("/token", data={"username": "", "password": "admin123"})
        assert response.status_code == 400


class TestAuthProtectedEndpoints:
    def test_students_endpoint_requires_auth(self, client):
        response = client.get("/api/students")
        assert response.status_code == 401
    
    def test_students_endpoint_rejects_invalid_token(self, client):
        response = client.get("/api/students", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401
    
    def test_students_endpoint_rejects_malformed_header(self, client):
        response = client.get("/api/students", headers={"Authorization": "NotBearer token"})
        assert response.status_code == 401
    
    def test_students_endpoint_accepts_valid_token(self, client, admin_user, auth_headers):
        response = client.get("/api/students", headers=auth_headers)
        assert response.status_code == 200
    
    def test_add_student_requires_auth(self, client):
        response = client.post("/api/students", json={"name": "Alice"})
        assert response.status_code == 401
    
    def test_add_grade_requires_auth(self, client, student):
        response = client.post("/api/grades", json={"student_name": "John", "score": 90})
        assert response.status_code == 401
    
    def test_add_behavior_requires_auth(self, client, student):
        response = client.post("/api/behaviors", json={"student_name": "John", "note": "Good", "behavior_type": "positive"})
        assert response.status_code == 401
    
    def test_mark_attendance_requires_auth(self, client, student):
        response = client.post("/api/attendance", json={"student_name": "John", "status": "present"})
        assert response.status_code == 401
    
    def test_report_requires_auth(self, client, student):
        response = client.get("/api/students/John/report")
        assert response.status_code == 401
    
    def test_pdf_endpoint_requires_auth(self, client, student):
        response = client.post("/api/students/John/report/pdf")
        assert response.status_code == 401


class TestAuthMultipleUsers:
    def test_different_user_cannot_access_others_data(self, client, second_user):
        response = client.post("/token", data={"username": "teacher", "password": "teacher456"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        response = client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_admin_can_access_all_data(self, client, admin_user, student, auth_headers):
        response = client.get("/api/students", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestAuthTokenExpiry:
    def test_token_contains_expected_payload(self, client, admin_user):
        import base64
        response = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = response.json()["access_token"]
        
        parts = token.split(".")
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        import json
        data = json.loads(decoded)
        
        assert data["sub"] == "admin"
        assert "exp" in data


class TestAuthCommandEndpoint:
    def test_command_requires_auth(self, client):
        response = client.post("/api/command", json={"command": "/add-student Bob"})
        assert response.status_code == 401
    
    def test_command_works_with_valid_token(self, client, admin_user, auth_headers):
        response = client.post("/api/command", json={"command": "/add-student Bob"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestInitAdmin:
    def test_init_admin_works(self, client):
        response = client.post("/api/init-admin?username=newadmin&password=newpass123")
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_init_admin_fails_for_existing_user(self, client, admin_user):
        response = client.post("/api/init-admin?username=admin&password=pass")
        assert response.status_code == 200
        assert response.json()["success"] is False
    
    def test_can_login_after_init_admin(self, client):
        client.post("/api/init-admin?username=testuser&password=testpass")
        response = client.post("/token", data={"username": "testuser", "password": "testpass"})
        assert response.status_code == 200


class TestSetupPage:
    def test_setup_page_shows_when_no_admin(self, client):
        response = client.get("/setup")
        assert response.status_code == 200
        assert "setup.html" in response.text or "Setup" in response.text
    
    def test_setup_page_redirects_when_admin_exists(self, client, admin_user):
        response = client.get("/setup", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/"
    
    def test_setup_page_renders_form(self, client):
        response = client.get("/setup")
        assert response.status_code == 200
        assert "username" in response.text.lower()
        assert "password" in response.text.lower()