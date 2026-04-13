from typing import Optional
from pydantic import BaseModel


class CommandRequest(BaseModel):
    command: str


def parse_command(command: str) -> dict:
    parts = command.strip().split()
    if not parts or not parts[0].startswith("/"):
        return {"action": "invalid", "message": "Commands must start with /"}
    
    cmd = parts[0][1:].lower()
    args = parts[1:]
    
    def _name_and_rest(args, *stop_words):
        name_parts = []
        rest_start = len(args)
        for i, arg in enumerate(args):
            if arg.startswith("--") or arg.lower() in stop_words:
                rest_start = i
                break
            parts_after = args[i+1:]
            for pa in parts_after:
                try:
                    float(pa)
                    rest_start = i + 1
                    return " ".join(args[:rest_start]), args[rest_start:]
                except ValueError:
                    pass
            name_parts.append(arg)
        else:
            return " ".join(args[:rest_start]), args[rest_start:]
        return " ".join(args[:rest_start]), args[rest_start:]
    
    if cmd in ("addstudent", "add", "add-student"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /add-student <name> [--year \"Grade N\"]"}
        name_parts = []
        year = None
        details = None
        capture_year = False
        capture_details = False
        year_parts = []
        details_parts = []
        
        for arg in args:
            if arg in ("--year", "--yr", "-y"):
                capture_year = True
                capture_details = False
                year_parts = []
            elif arg == "--details":
                capture_year = False
                capture_details = True
                details_parts = []
            elif arg.startswith("--"):
                capture_year = False
                capture_details = False
            elif capture_year:
                year_parts.append(arg)
            elif capture_details:
                details_parts.append(arg)
            else:
                name_parts.append(arg)
        
        student_name = " ".join(name_parts).strip('"')
        year = " ".join(year_parts).strip('"') if year_parts else None
        details = " ".join(details_parts).strip('"') if details_parts else None
        
        return {"action": "add_student", "name": student_name, "year": year, "details": details}
    
    if cmd == "grade":
        if len(args) < 2:
            return {"action": "error", "message": "Usage: /grade <name> <score> [--subject Math] [--date YYYY-MM-DD]"}
        score = None
        score_idx = None
        for i, arg in enumerate(args):
            if arg.startswith("--"):
                break
            try:
                score = float(arg)
                score_idx = i
                break
            except ValueError:
                continue
        if score is None or score_idx is None:
            return {"action": "error", "message": "Score must be a number"}
        name = " ".join(args[:score_idx])
        if not name:
            return {"action": "error", "message": "Usage: /grade <name> <score> [--subject Math] [--date YYYY-MM-DD]"}
        subject = "General"
        date_str = None
        rest = args[score_idx + 1:]
        for i, arg in enumerate(rest):
            if arg == "--subject" and i + 1 < len(rest):
                subject = rest[i + 1]
            elif arg in ("--date", "--at") and i + 1 < len(rest):
                date_str = rest[i + 1]
        return {"action": "add_grade", "student_name": name, "score": score, "subject": subject, "date": date_str}
    
    if cmd in ("behavior", "behave"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /behavior <name> <type> [--note \"text\"] [--date YYYY-MM-DD]"}
        behavior_type = "neutral"
        note = ""
        date_str = None
        name_parts = []
        behavior_keywords = {"positive", "negative", "neutral"}
        for arg in args:
            if arg.startswith("--"):
                if arg in ("--date", "--at"):
                    pass
                else:
                    break
            elif arg.lower() in behavior_keywords and not name_parts:
                pass
            elif arg.lower() in behavior_keywords:
                behavior_type = arg.lower()
                break
            elif arg in ("--date", "--at"):
                break
            else:
                name_parts.append(arg)
        name = " ".join(name_parts)
        if not name:
            return {"action": "error", "message": "Usage: /behavior <name> <type> [--note \"text\"] [--date YYYY-MM-DD]"}
        for i, arg in enumerate(args):
            if arg == "--note" and i + 1 < len(args):
                note = " ".join(args[i+1:]).strip('"')
            elif arg in ("--date", "--at") and i + 1 < len(args):
                date_str = args[i + 1]
            elif arg.lower() in behavior_keywords:
                behavior_type = arg.lower()
        return {"action": "add_behavior", "student_name": name, "behavior_type": behavior_type, "note": note, "date": date_str}
    
    if cmd in ("attendance", "attend"):
        if len(args) < 2:
            return {"action": "error", "message": "Usage: /attendance <name> present|absent|late [--date YYYY-MM-DD]"}
        status_keywords = {"present", "absent", "late"}
        status = None
        name_parts = []
        date_str = None
        for i, arg in enumerate(args):
            if arg.startswith("--"):
                if arg in ("--date", "--at") and i + 1 < len(args):
                    date_str = args[i + 1]
                continue
            if arg.lower() in status_keywords:
                status = arg.lower()
                break
            name_parts.append(arg)
        if not name_parts:
            return {"action": "error", "message": "Usage: /attendance <name> present|absent|late [--date YYYY-MM-DD]"}
        if status is None:
            return {"action": "error", "message": "Usage: /attendance <name> present|absent|late [--date YYYY-MM-DD]"}
        name = " ".join(name_parts)
        for i, arg in enumerate(args):
            if arg in ("--date", "--at") and i + 1 < len(args):
                date_str = args[i + 1]
        return {"action": "mark_attendance", "student_name": name, "status": status, "date": date_str}
    
    if cmd in ("homework", "hw"):
        if len(args) < 2:
            return {"action": "error", "message": "Usage: /homework <name> <title> [--due YYYY-MM-DD] [--status <status>]"}
        student_name = args[0]
        title_parts = []
        due_date = None
        status = "pending"
        capture_status = False
        
        for i, arg in enumerate(args):
            if i == 0:
                continue
            if arg in ("--due", "--by"):
                capture_status = False
                if i + 1 < len(args):
                    due_date = args[i + 1]
            elif arg == "--status":
                capture_status = True
                status = None
            elif capture_status:
                if arg.startswith("--"):
                    capture_status = False
                    i -= 1
                elif status is None:
                    status = arg.strip('"')
                else:
                    status += " " + arg.strip('"')
            elif not arg.startswith("--"):
                title_parts.append(arg)
        
        title = " ".join(title_parts)
        if title.startswith('"') and title.endswith('"'):
            title = title[1:-1]
        if status is None:
            status = "pending"
        
        return {"action": "add_homework", "student_name": student_name, "title": title, "due_date": due_date, "status": status}
    
    if cmd == "activity":
        if len(args) < 3:
            return {"action": "error", "message": "Usage: /activity <name> <type> <status> [--date YYYY-MM-DD]"}
        valid_statuses = ["yes", "no"]
        status = None
        status_idx = None
        for i in range(len(args) - 1, -1, -1):
            if args[i].lower() in valid_statuses:
                status = args[i].lower()
                status_idx = i
                break
        if status is None:
            return {"action": "error", "message": f"Invalid status. Use: yes or no"}
        if status_idx < 1:
            return {"action": "error", "message": "Usage: /activity <name> <type> <status> [--date YYYY-MM-DD]"}
        activity_type = args[status_idx - 1].lower()
        student_name = " ".join(args[:status_idx - 1])
        if not student_name:
            return {"action": "error", "message": "Usage: /activity <name> <type> <status> [--date YYYY-MM-DD]"}
        date_str = None
        for i, arg in enumerate(args):
            if arg in ("--date", "--at") and i + 1 < len(args):
                date_str = args[i + 1]
        return {"action": "add_activity", "student_name": student_name, "activity_type": activity_type, "status": status, "date": date_str}
    
    if cmd in ("report", "stats"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /report <name> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--pdf]"}
        name_parts = []
        date_from = None
        date_to = None
        generate_pdf = False
        for i, arg in enumerate(args):
            if arg == "--from" and i + 1 < len(args):
                date_from = args[i + 1]
            elif arg == "--to" and i + 1 < len(args):
                date_to = args[i + 1]
            elif arg == "--date" and i + 1 < len(args):
                date_from = date_to = args[i + 1]
            elif arg == "--pdf":
                generate_pdf = True
            elif not arg.startswith("--"):
                prev = args[i-1] if i > 0 else ""
                if prev not in ("--from", "--to", "--date", "--at"):
                    name_parts.append(arg)
        student_name = " ".join(name_parts)
        return {"action": "get_report", "student_name": student_name, "date_from": date_from, "date_to": date_to, "pdf": generate_pdf}
    
    if cmd in ("dashboard", "dash", "d"):
        if len(args) < 1:
            return {"action": "list_dashboard"}
        name_parts = []
        for arg in args:
            if not arg.startswith("--"):
                name_parts.append(arg)
        return {"action": "open_dashboard", "student_name": " ".join(name_parts)}
    
    if cmd == "help":
        message = """Available commands:
/add-student <name> [--year "Grade N"] - Add a new student (e.g., /add-student John --year "Grade 8")
/grade <name> <score> [--subject <subject>] [--date YYYY-MM-DD] - Add a grade (use name or ID like STU-001)
/behavior <name> <type> [--note "note"] [--date YYYY-MM-DD] - Record behavior (positive/negative/neutral)
/attendance <name> present|absent|late [--date YYYY-MM-DD] - Mark attendance
/homework <name> <title> [--due YYYY-MM-DD] [--status <status>] - Add homework
/activity <name> <type> <status> [--date YYYY-MM-DD] - Record activity (type: any; status: yes/no)
/report <name> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--pdf] - Get student report (use name or ID)
/dashboard <name> - Open student dashboard (use name or ID)
/dashboard - List all students
/help - Show this help"""
        return {"action": "help", "message": message}
    
    return {"action": "invalid", "message": f"Unknown command: /{cmd}. Type /help for available commands."}