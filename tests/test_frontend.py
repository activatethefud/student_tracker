import pytest
from jinja2 import Environment, FileSystemLoader, exceptions
from datetime import datetime
import os


class TestFrontend:
    @classmethod
    def setup_class(cls):
        cls.static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
        cls.env = Environment(loader=FileSystemLoader(cls.static_dir))
    
    def test_index_template_compiles(self):
        """Verify index.html template compiles without errors"""
        template = self.env.get_template('index.html')
        assert template is not None
    
    def test_index_template_renders(self):
        """Verify template can render with required context"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        assert 'Student Tracker' in rendered
        assert 'chat-box' in rendered
        assert 'command-input' in rendered
    
    def test_setup_template_compiles(self):
        """Verify setup.html template compiles without errors"""
        template = self.env.get_template('setup.html')
        assert template is not None
    
    def test_index_has_required_elements(self):
        """Verify index.html has all required UI elements"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        # Auth elements
        assert 'login-modal' in rendered
        assert 'login-form' in rendered
        assert 'auth-section' in rendered
        
        # Chat elements
        assert 'chat-box' in rendered
        assert 'command-input' in rendered
        
        # Quick reference buttons
        assert '/add-student' in rendered
        assert '/grade' in rendered
        assert '/behavior' in rendered
        assert '/homework' in rendered
        assert '/attendance' in rendered
        assert '/report' in rendered
    
    def test_index_mobile_responsive_classes(self):
        """Verify mobile-responsive classes are present"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        assert 'max-w-sm' in rendered
        assert 'sm:max-w-md' in rendered
        assert 'md:max-w-2xl' in rendered
        assert 'lg:max-w-3xl' in rendered
    
    def test_index_has_javascript(self):
        """Verify JavaScript functions are present"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        assert 'function showLogin()' in rendered
        assert 'function hideLogin()' in rendered
        assert 'function sendCommand()' in rendered
        assert 'function quickCommand(' in rendered
        assert 'function logout()' in rendered
    
    def test_login_modal_structure(self):
        """Verify login modal has required fields"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        assert 'login-username' in rendered
        assert 'login-password' in rendered
        assert 'master-password' in rendered
        assert 'reset-section' in rendered
    
    def test_command_input_functionality(self):
        """Verify command input has enter key handler"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        assert 'keypress' in rendered
        assert 'sendCommand()' in rendered
    
    def test_all_quick_buttons_present(self):
        """Verify all quick command buttons are present"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        buttons = ['/add-student', '/grade', '/behavior', '/homework', '/attendance', '/report']
        for btn in buttons:
            assert btn in rendered
    
    def test_message_handling_exists(self):
        """Verify addMessage function exists"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        assert 'function addMessage(' in rendered
    
    def test_pdf_download_handling(self):
        """Verify PDF download handling exists"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        
        assert 'application/pdf' in rendered
        assert 'download' in rendered
    
    def test_setup_template_renders(self):
        """Verify setup.html can render"""
        template = self.env.get_template('setup.html')
        rendered = template.render()
        assert 'Setup' in rendered
        assert 'username' in rendered.lower()
        assert 'password' in rendered.lower()
    
    def test_dashboard_template_compiles(self):
        """Verify dashboard.html template compiles without errors"""
        template = self.env.get_template('dashboard.html')
        assert template is not None
    
    def test_dashboard_renders_student_data(self):
        """Verify dashboard template renders student data fields"""
        from datetime import datetime
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': 'Test'},
            grades=[],
            behaviors=[],
            attendances=[],
            homeworks=[],
            avg_grade=85.0,
            attendance_pct=90.0,
            pending_hw=2,
            submitted_hw=5,
            other_hw=1
        )
        assert 'John' in rendered
        assert '85.0' in rendered
        assert 'Grades' in rendered
        assert 'Behaviors' in rendered
        assert 'Attendance' in rendered
        assert 'Homework' in rendered
    
    def test_students_list_template_compiles(self):
        """Verify students.html template compiles"""
        template = self.env.get_template('students.html')
        assert template is not None
    
    def test_students_list_renders_student_names(self):
        """Verify students list shows student names"""
        template = self.env.get_template('students.html')
        rendered = template.render(request={}, students=[
            {'name': 'Alice', 'details': None},
            {'name': 'Bob', 'details': 'Test student'}
        ])
        assert 'Alice' in rendered
        assert 'Bob' in rendered
    
    def test_dashboard_delete_confirmation_ui(self):
        """Verify delete confirmation UI elements present"""
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': ''},
            grades=[], behaviors=[], attendances=[], homeworks=[],
            avg_grade=0, attendance_pct=0, pending_hw=0, submitted_hw=0, other_hw=0
        )
        assert 'confirmDelete' in rendered
        assert 'Delete' in rendered
    
    def test_dashboard_edit_modal_structure(self):
        """Verify edit modal structure present"""
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': ''},
            grades=[], behaviors=[], attendances=[], homeworks=[],
            avg_grade=0, attendance_pct=0, pending_hw=0, submitted_hw=0, other_hw=0
        )
        assert 'edit-modal' in rendered
        assert 'showEditModal' in rendered
        assert 'edit-form' in rendered
    
    def test_dashboard_has_edit_delete_buttons(self):
        """Verify edit and delete buttons present in dashboard"""
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': ''},
            grades=[{'id': 1, 'score': 90, 'subject': 'Math', 'created_at': datetime.now()}],
            behaviors=[],
            attendances=[],
            homeworks=[],
            avg_grade=90, attendance_pct=100, pending_hw=0, submitted_hw=0, other_hw=0
        )
        assert 'Edit' in rendered
        assert 'Delete Student' in rendered
    
    def test_index_has_dashboard_button(self):
        """Verify quick reference has Dashboard button"""
        template = self.env.get_template('index.html')
        rendered = template.render(request={}, students=[], admin_exists=True)
        assert '/dashboard' in rendered
    
    def test_dashboard_has_login_modal(self):
        """Verify dashboard has login modal"""
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': ''},
            grades=[], behaviors=[], attendances=[], homeworks=[],
            avg_grade=0, attendance_pct=0, pending_hw=0, submitted_hw=0, other_hw=0
        )
        assert 'login-modal' in rendered
        assert 'login-form' in rendered
    
    def test_dashboard_has_login_functionality(self):
        """Verify dashboard has login/logout functions"""
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': ''},
            grades=[], behaviors=[], attendances=[], homeworks=[],
            avg_grade=0, attendance_pct=0, pending_hw=0, submitted_hw=0, other_hw=0
        )
        assert 'function showLogin()' in rendered
        assert 'function logout()' in rendered
    
    def test_dashboard_auth_section_present(self):
        """Verify dashboard has auth section"""
        template = self.env.get_template('dashboard.html')
        rendered = template.render(
            request={},
            student={'name': 'John', 'details': ''},
            grades=[], behaviors=[], attendances=[], homeworks=[],
            avg_grade=0, attendance_pct=0, pending_hw=0, submitted_hw=0, other_hw=0
        )
        assert 'auth-section' in rendered
    
    def test_students_list_has_login_modal(self):
        """Verify students list has login modal"""
        template = self.env.get_template('students.html')
        rendered = template.render(request={}, students=[])
        assert 'login-modal' in rendered