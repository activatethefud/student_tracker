import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db, failed_login_attempts
from app.models import Base, Student, User
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


class TestLoginLockout:
    def test_first_failed_login_tracked(self, client, admin_user):
        client.post("/token", data={"username": "admin", "password": "wrong"})
        assert "admin" in failed_login_attempts
        assert failed_login_attempts["admin"]["count"] == 1
    
    def test_multiple_failed_logins_tracked(self, client, admin_user):
        client.post("/token", data={"username": "admin", "password": "wrong"})
        client.post("/token", data={"username": "admin", "password": "wrong"})
        client.post("/token", data={"username": "admin", "password": "wrong"})
        assert failed_login_attempts["admin"]["count"] == 3
    
    def test_successful_login_clears_attempts(self, client, admin_user):
        failed_login_attempts["admin"] = {"count": 2, "time": None}
        response = client.post("/token", data={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        assert "admin" not in failed_login_attempts
    
    def test_account_locked_after_3_attempts(self, client, admin_user):
        failed_login_attempts["admin"] = {"count": 3, "time": None}
        
        response = client.post("/token", data={"username": "admin", "password": "any"})
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()
    
    def test_wrong_master_password_after_lock(self, client, admin_user):
        failed_login_attempts["admin"] = {"count": 3, "time": None}
        
        response = client.post("/token", data={"username": "admin", "password": "wrongmaster"})
        assert response.status_code == 423
    
    def test_correct_master_password_resets_admin(self, client, admin_user):
        failed_login_attempts["admin"] = {"count": 3, "time": None}
        
        response = client.post("/token", data={"username": "admin", "password": "RESET-admin-2024"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        login_response = client.post("/token", data={"username": "admin", "password": "RESET-admin-2024"})
        assert login_response.status_code == 200
    
    def test_different_username_tracked_separately(self, client, admin_user):
        client.post("/token", data={"username": "admin", "password": "wrong"})
        client.post("/token", data={"username": "admin", "password": "wrong"})
        
        client.post("/token", data={"username": "nonexistent", "password": "wrong"})
        
        assert failed_login_attempts["admin"]["count"] == 2
        assert failed_login_attempts["nonexistent"]["count"] == 1
    
    def test_locked_user_gets_locked_message(self, client, admin_user):
        failed_login_attempts["admin"] = {"count": 3, "time": None}
        
        response = client.post("/token", data={"username": "admin", "password": "wrong"})
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()
    
    def test_successful_login_works(self, client, admin_user):
        response = client.post("/token", data={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_empty_password_at_locked_state(self, client, admin_user):
        failed_login_attempts["admin"] = {"count": 3, "time": None}
        
        response = client.post("/token", data={"username": "admin", "password": ""})
        assert response.status_code == 423
        assert "master password" in response.json()["detail"].lower()