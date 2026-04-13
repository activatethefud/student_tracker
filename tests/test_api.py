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
def auth_headers(client, admin_user):
    login = client.post("/token", data={"username": "admin", "password": "test"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
    from app.models import generate_student_id
    s = Student(name="John", student_id=generate_student_id(db))
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


class TestHomeworkAPI:
    def test_homework_command_adds_homework(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": '/homework John "Read chapter 5"'},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Read chapter 5" in data["message"]
    
    def test_homework_command_with_due_date(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": '/homework John "Math worksheet" --due 2024-04-15'},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "2024-04-15" in data["message"]
    
    def test_homework_command_with_custom_status(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": '/homework John "Essay" --status "in progress"'},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "in progress" in data["message"]
    
    def test_homework_command_student_not_found(self, client, admin_user):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": '/homework NonExistent "Test"'},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_homework_included_in_report(self, client, admin_user, student):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        client.post(
            "/api/command",
            json={"command": '/homework John "Test homework"'},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        response = client.post(
            "/api/command",
            json={"command": "/report John"},
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()
        assert "Homework" in data["message"]


class TestDashboardAPI:
    def test_get_students_list(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.get("/students", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "John" in response.text
    
    def test_get_student_dashboard(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.get("/student/John", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "John" in response.text
        assert "Grades" in response.text
    
    def test_get_student_dashboard_not_found(self, client, admin_user):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.get("/student/NonExistent", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404
    
    def test_delete_grade(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        grade_response = client.post(
            "/api/command",
            json={"command": "/grade John 90 --subject Math"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        from app.models import Grade
        grade = db.query(Grade).filter(Grade.student_id == student.id).first()
        
        response = client.delete(f"/api/grades/{grade.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_delete_behavior(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Behavior
        behavior = Behavior(student_id=student.id, note="Test", behavior_type="positive")
        db.add(behavior)
        db.commit()
        
        response = client.delete(f"/api/behaviors/{behavior.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_delete_attendance(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Attendance
        from datetime import date
        attendance = Attendance(student_id=student.id, status="present", date=date.today())
        db.add(attendance)
        db.commit()
        
        response = client.delete(f"/api/attendance/{attendance.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_delete_homework(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Homework
        homework = Homework(student_id=student.id, title="Test", status="pending")
        db.add(homework)
        db.commit()
        
        response = client.delete(f"/api/homework/{homework.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_delete_student_cascade(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Grade
        grade = Grade(student_id=student.id, score=90, subject="Math")
        db.add(grade)
        db.commit()
        
        response = client.delete("/api/students/John", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        from app.models import Student
        assert db.query(Student).filter(Student.name == "John").first() is None
    
    def test_delete_student_by_id(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.delete("/api/students/STU-001", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "Deleted student John" in response.json()["message"]
        
        from app.models import Student
        assert db.query(Student).filter(Student.name == "John").first() is None
    
    def test_delete_student_by_id_prefix(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.delete("/api/students/STU-001", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        from app.models import Student
        assert db.query(Student).filter(Student.name == "John").first() is None
    
    def test_delete_student_with_surname(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Student
        student = Student(name="Sofija Stojanovic", year="Grade 8")
        db.add(student)
        db.commit()
        
        response = client.delete("/api/students/Sofija Stojanovic", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "Deleted student Sofija Stojanovic" in response.json()["message"]
        
        assert db.query(Student).filter(Student.name == "Sofija Stojanovic").first() is None
    
    def test_delete_nonexistent_student_returns_404(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.delete("/api/students/NonExistent", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404
    
    def test_update_grade(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Grade
        grade = Grade(student_id=student.id, score=90, subject="Math")
        db.add(grade)
        db.commit()
        
        response = client.put(
            f"/api/grades/{grade.id}",
            json={"score": 95, "subject": "Science"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        db.refresh(grade)
        assert grade.score == 95
        assert grade.subject == "Science"
    
    def test_update_student_details(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.put(
            "/api/students/John",
            json={"name": "Johnny", "details": "Updated details"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        db.refresh(student)
        assert student.name == "Johnny"
        assert student.details == "Updated details"
    
    def test_students_page_loads_without_auth(self, client):
        response = client.get("/students")
        assert response.status_code == 200
    
    def test_student_dashboard_loads_without_auth(self, client):
        response = client.get("/student/John")
        assert response.status_code in [200, 404]
    
    def test_delete_nonexistent_grade_returns_404(self, client, admin_user):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.delete("/api/grades/99999", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404


class TestStudentIDAndYear:
    def test_create_student_with_year(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.post(
            "/api/command",
            json={"command": "/add-student Alice --year Grade 8"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Grade 8" in data["message"]
        assert "STU-" in data["message"]
    
    def test_student_id_generated(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        client.post(
            "/api/command",
            json={"command": "/add-student Bob --year Grade 1"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        response = client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
        students = response.json()
        # Check it's a list and contains expected data
        assert isinstance(students, list)
        bob = next((s for s in students if s["name"] == "Bob"), None)
        assert bob is not None
        assert bob.get("year") == "Grade 1"
    
    def test_report_with_student_id(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        # First add a grade so report has content
        client.post(
            "/api/command",
            json={"command": "/grade John 90"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get student to find ID
        from app.models import Student
        db.refresh(student)
        student_id = student.student_id
        
        # Report with student ID
        response = client.post(
            "/api/command",
            json={"command": f"/report {student_id}"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "John" in data["message"]
    
    def test_report_with_prefix_id(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        from app.models import Student
        db.refresh(student)
        student_id = student.student_id
        prefix = student_id[:-1]  # Remove last character
        
        response = client.post(
            "/api/command",
            json={"command": f"/report {prefix}"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_student_year(self, client, admin_user, student, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        response = client.put(
            "/api/students/John",
            json={"year": "Grade 9"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        db.refresh(student)
        assert student.year == "Grade 9"
    
    def test_ambiguous_name_resolution(self, client, admin_user, db):
        login = client.post("/token", data={"username": "admin", "password": "test"})
        token = login.json()["access_token"]
        
        # Create two students with same name but different years
        client.post(
            "/api/command",
            json={"command": '/add-student TestStudent --year "Grade 8"'},
            headers={"Authorization": f"Bearer {token}"}
        )
        client.post(
            "/api/command",
            json={"command": '/add-student TestStudent --year "Grade 9"'},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Try to report - should handle gracefully
        response = client.post(
            "/api/command",
            json={"command": "/report TestStudent"},
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()
        # Should either work (if exact match by some logic) or show error with options
        # The behavior depends on implementation
        assert data["success"] is True or "Multiple students" in data.get("message", "")