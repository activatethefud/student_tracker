import pytest
from app.commands import parse_command


class TestParseCommand:
    def test_add_student(self):
        result = parse_command("/add-student John")
        assert result["action"] == "add_student"
        assert result["name"] == "John"
    
    def test_add_student_with_details(self):
        result = parse_command("/add-student John --details \"A good student\"")
        assert result["action"] == "add_student"
        assert result["name"] == "John"
    
    def test_grade_basic(self):
        result = parse_command("/grade John 90")
        assert result["action"] == "add_grade"
        assert result["student_name"] == "John"
        assert result["score"] == 90
        assert result["subject"] == "General"
    
    def test_grade_with_subject(self):
        result = parse_command("/grade John 95 --subject Math")
        assert result["action"] == "add_grade"
        assert result["subject"] == "Math"
    
    def test_grade_invalid_score(self):
        result = parse_command("/grade John abc")
        assert result["action"] == "error"
    
    def test_behavior_positive(self):
        result = parse_command("/behavior John positive --note \"Helped peer\"")
        assert result["action"] == "add_behavior"
        assert result["student_name"] == "John"
        assert result["behavior_type"] == "positive"
        assert result["note"] == "Helped peer"
    
    def test_behavior_negative(self):
        result = parse_command("/behavior John negative --note \"Late to class\"")
        assert result["action"] == "add_behavior"
        assert result["behavior_type"] == "negative"
    
    def test_behavior_default(self):
        result = parse_command("/behavior John")
        assert result["action"] == "add_behavior"
        assert result["behavior_type"] == "neutral"
    
    def test_attendance_present(self):
        result = parse_command("/attendance John present")
        assert result["action"] == "mark_attendance"
        assert result["student_name"] == "John"
        assert result["status"] == "present"
    
    def test_attendance_absent(self):
        result = parse_command("/attendance John absent")
        assert result["status"] == "absent"
    
    def test_attendance_late(self):
        result = parse_command("/attendance John late")
        assert result["status"] == "late"
    
    def test_report(self):
        result = parse_command("/report John")
        assert result["action"] == "get_report"
        assert result["student_name"] == "John"
    
    def test_report_with_from_date(self):
        result = parse_command("/report John --from 2024-01-01")
        assert result["action"] == "get_report"
        assert result["student_name"] == "John"
        assert result["date_from"] == "2024-01-01"
    
    def test_report_with_to_date(self):
        result = parse_command("/report John --to 2024-12-31")
        assert result["action"] == "get_report"
        assert result["date_to"] == "2024-12-31"
    
    def test_report_with_date_range(self):
        result = parse_command("/report John --from 2024-01-01 --to 2024-12-31")
        assert result["date_from"] == "2024-01-01"
        assert result["date_to"] == "2024-12-31"
    
    def test_report_with_pdf_flag(self):
        result = parse_command("/report John --pdf")
        assert result["pdf"] is True
    
    def test_report_with_date_and_pdf(self):
        result = parse_command("/report John --from 2024-01-01 --pdf")
        assert result["date_from"] == "2024-01-01"
        assert result["pdf"] is True
    
    def test_help_command(self):
        result = parse_command("/help")
        assert result["action"] == "help"
    
    def test_invalid_command(self):
        result = parse_command("/unknown John")
        assert result["action"] == "invalid"
    
    def test_no_slash(self):
        result = parse_command("just some text")
        assert result["action"] == "invalid"
    
    def test_empty_command(self):
        result = parse_command("")
        assert result["action"] == "invalid"
    
    def test_missing_args_add_student(self):
        result = parse_command("/add-student")
        assert result["action"] == "error"
    
    def test_missing_args_grade(self):
        result = parse_command("/grade John")
        assert result["action"] == "error"
    
    def test_missing_args_attendance(self):
        result = parse_command("/attendance John")
        assert result["action"] == "error"
    
    def test_missing_args_report(self):
        result = parse_command("/report")
        assert result["action"] == "error"