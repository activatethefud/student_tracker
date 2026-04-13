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
    
    def test_grade_with_date(self):
        result = parse_command("/grade John 90 --date 2024-03-15")
        assert result["action"] == "add_grade"
        assert result["date"] == "2024-03-15"
    
    def test_grade_with_subject_and_date(self):
        result = parse_command("/grade John 85 --subject Science --date 2024-02-01")
        assert result["subject"] == "Science"
        assert result["date"] == "2024-02-01"
    
    def test_behavior_with_date(self):
        result = parse_command("/behavior John positive --note \"Good work\" --date 2024-03-20")
        assert result["action"] == "add_behavior"
        assert result["date"] == "2024-03-20"
    
    def test_attendance_with_date(self):
        result = parse_command("/attendance John present --date 2024-03-10")
        assert result["action"] == "mark_attendance"
        assert result["date"] == "2024-03-10"
    
    def test_attendance_with_at_alias(self):
        result = parse_command("/attendance John late --at 2024-01-15")
        assert result["date"] == "2024-01-15"

    def test_homework_basic(self):
        result = parse_command('/homework John "Read chapter 5"')
        assert result["action"] == "add_homework"
        assert result["student_name"] == "John"
        assert result["title"] == "Read chapter 5"
        assert result["status"] == "pending"
    
    def test_homework_with_due_date(self):
        result = parse_command('/homework John "Read chapter 5" --due 2024-04-15')
        assert result["action"] == "add_homework"
        assert result["due_date"] == "2024-04-15"
    
    def test_homework_with_status(self):
        result = parse_command('/homework John "Math worksheet" --status submitted')
        assert result["action"] == "add_homework"
        assert result["status"] == "submitted"
    
    def test_homework_with_due_and_status(self):
        result = parse_command('/homework John "Essay" --due 2024-05-01 --status submitted')
        assert result["due_date"] == "2024-05-01"
        assert result["status"] == "submitted"
    
    def test_homework_missing_args(self):
        result = parse_command("/homework John")
        assert result["action"] == "error"
    
    def test_homework_custom_status(self):
        result = parse_command('/homework John "Test" --status "in progress"')
        assert result["action"] == "add_homework"
        assert result["status"] == "in progress"
    
    def test_homework_title_with_quotes(self):
        result = parse_command('/homework John "Chapter 5: Pages 1-10"')
        assert result["action"] == "add_homework"
        assert result["title"] == "Chapter 5: Pages 1-10"
    
    def test_homework_no_title(self):
        result = parse_command("/homework John")
        assert result["action"] == "error"
    
    def test_homework_by_alias(self):
        result = parse_command('/homework John "Test" --by 2024-12-01')
        assert result["action"] == "add_homework"
        assert result["due_date"] == "2024-12-01"
    
    def test_homework_default_status_when_explicit(self):
        result = parse_command('/homework John "Test" --status')
        assert result["action"] == "add_homework"
        assert result["status"] == "pending"
    
    def test_dashboard_command_with_name(self):
        result = parse_command("/dashboard John")
        assert result["action"] == "open_dashboard"
        assert result["student_name"] == "John"
    
    def test_dashboard_command_no_name(self):
        result = parse_command("/dashboard")
        assert result["action"] == "list_dashboard"
    
    def test_dashboard_alias_dash(self):
        result = parse_command("/dash John")
        assert result["action"] == "open_dashboard"
        assert result["student_name"] == "John"
    
    def test_activity_taking_notes_yes(self):
        result = parse_command("/activity John taking-notes yes")
        assert result["action"] == "add_activity"
        assert result["student_name"] == "John"
        assert result["activity_type"] == "taking-notes"
        assert result["status"] == "yes"
    
    def test_activity_participation_no(self):
        result = parse_command("/activity John participation no")
        assert result["action"] == "add_activity"
        assert result["activity_type"] == "participation"
        assert result["status"] == "no"
    
    def test_activity_with_date(self):
        result = parse_command("/activity John taking-notes yes --date 2024-03-20")
        assert result["action"] == "add_activity"
        assert result["date"] == "2024-03-20"
    
    def test_activity_invalid_type(self):
        result = parse_command("/activity John custom-type yes")
        assert result["action"] == "add_activity"
        assert result["activity_type"] == "custom-type"
    
    def test_activity_invalid_status(self):
        result = parse_command("/activity John taking-notes maybe")
        assert result["action"] == "error"
        assert "Invalid status" in result["message"]
    
    def test_activity_missing_args(self):
        result = parse_command("/activity John")
        assert result["action"] == "error"
    
    def test_activity_partial_args(self):
        result = parse_command("/activity John taking-notes")
        assert result["action"] == "error"
    
    def test_add_student_multi_word_name(self):
        result = parse_command("/add-student Marko Stefanovic")
        assert result["action"] == "add_student"
        assert result["name"] == "Marko Stefanovic"
    
    def test_add_student_multi_word_name_with_year(self):
        result = parse_command('/add-student Marko Stefanovic --year "Grade 8"')
        assert result["action"] == "add_student"
        assert result["name"] == "Marko Stefanovic"
        assert result["year"] == "Grade 8"
    
    def test_add_student_three_word_name(self):
        result = parse_command("/add-student Ana Maria Garcia")
        assert result["action"] == "add_student"
        assert result["name"] == "Ana Maria Garcia"
    
    def test_grade_multi_word_name(self):
        result = parse_command("/grade Marko Stefanovic 90 --subject Math")
        assert result["action"] == "add_grade"
        assert result["student_name"] == "Marko Stefanovic"
        assert result["score"] == 90
        assert result["subject"] == "Math"
    
    def test_attendance_multi_word_name(self):
        result = parse_command("/attendance Marko Stefanovic present --date 2024-01-01")
        assert result["action"] == "mark_attendance"
        assert result["student_name"] == "Marko Stefanovic"
        assert result["status"] == "present"
        assert result["date"] == "2024-01-01"
    
    def test_behavior_multi_word_name(self):
        result = parse_command("/behavior Marko Stefanovic positive --note \"Great work\"")
        assert result["action"] == "add_behavior"
        assert result["student_name"] == "Marko Stefanovic"
        assert result["behavior_type"] == "positive"
    
    def test_activity_multi_word_name(self):
        result = parse_command("/activity Marko Stefanovic taking-notes yes")
        assert result["action"] == "add_activity"
        assert result["student_name"] == "Marko Stefanovic"
        assert result["activity_type"] == "taking-notes"
        assert result["status"] == "yes"
    
    def test_report_multi_word_name(self):
        result = parse_command("/report Marko Stefanovic --pdf")
        assert result["action"] == "get_report"
        assert result["student_name"] == "Marko Stefanovic"
        assert result["pdf"] is True
    
    def test_dashboard_multi_word_name(self):
        result = parse_command("/dashboard Marko Stefanovic")
        assert result["action"] == "open_dashboard"
        assert result["student_name"] == "Marko Stefanovic"
    
    def test_activity_multi_word_name_with_date(self):
        result = parse_command("/activity Marko Stefanovic focus yes --date 2024-03-20")
        assert result["action"] == "add_activity"
        assert result["student_name"] == "Marko Stefanovic"
        assert result["activity_type"] == "focus"
        assert result["status"] == "yes"
        assert result["date"] == "2024-03-20"