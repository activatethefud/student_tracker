import pytest
from jinja2 import Environment, FileSystemLoader, exceptions
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