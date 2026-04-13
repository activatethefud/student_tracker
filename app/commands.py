from pydantic import BaseModel
from typing import Optional


class CommandRequest(BaseModel):
    command: str


def parse_command(command: str) -> dict:
    parts = command.strip().split()
    if not parts or not parts[0].startswith("/"):
        return {"action": "invalid", "message": "Commands must start with /"}
    
    cmd = parts[0][1:].lower()
    args = parts[1:]
    
    if cmd in ("addstudent", "add", "add-student"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /add-student <name>"}
        return {"action": "add_student", "name": args[0], "details": " ".join(args[2:]) if len(args) > 2 else None}
    
    if cmd == "grade":
        if len(args) < 2:
            return {"action": "error", "message": "Usage: /grade <name> <score> [--subject Math] [--date YYYY-MM-DD]"}
        name = args[0]
        try:
            score = float(args[1])
        except ValueError:
            return {"action": "error", "message": "Score must be a number"}
        subject = "General"
        date_str = None
        for i, arg in enumerate(args):
            if arg == "--subject" and i + 1 < len(args):
                subject = args[i + 1]
            elif arg in ("--date", "--at") and i + 1 < len(args):
                date_str = args[i + 1]
        return {"action": "add_grade", "student_name": name, "score": score, "subject": subject, "date": date_str}
    
    if cmd in ("behavior", "behave"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /behavior <name> <type> [--note \"text\"] [--date YYYY-MM-DD]"}
        name = args[0]
        behavior_type = "neutral"
        note = ""
        date_str = None
        for i, arg in enumerate(args):
            if arg == "--note" and i + 1 < len(args):
                note = " ".join(args[i+1:]).strip('"')
            elif arg in ("--date", "--at") and i + 1 < len(args):
                date_str = args[i + 1]
            elif arg in ("positive", "negative", "neutral"):
                behavior_type = arg
        return {"action": "add_behavior", "student_name": name, "behavior_type": behavior_type, "note": note, "date": date_str}
    
    if cmd in ("attendance", "attend"):
        if len(args) < 2:
            return {"action": "error", "message": "Usage: /attendance <name> present|absent|late [--date YYYY-MM-DD]"}
        date_str = None
        for i, arg in enumerate(args):
            if arg in ("--date", "--at") and i + 1 < len(args):
                date_str = args[i + 1]
        status_idx = 1 if args[1].lower() in ("present", "absent", "late") else 0
        if len(args) < 2 or args[status_idx].lower() not in ("present", "absent", "late"):
            return {"action": "error", "message": "Usage: /attendance <name> present|absent|late [--date YYYY-MM-DD]"}
        return {"action": "mark_attendance", "student_name": args[0], "status": args[status_idx].lower(), "date": date_str}
    
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
    
    if cmd in ("report", "stats"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /report <name> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--pdf]"}
        student_name = args[0]
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
        return {"action": "get_report", "student_name": student_name, "date_from": date_from, "date_to": date_to, "pdf": generate_pdf}
    
    if cmd in ("dashboard", "dash", "d"):
        if len(args) < 1:
            return {"action": "list_dashboard"}
        return {"action": "open_dashboard", "student_name": args[0]}
    
    if cmd == "help":
        return {"action": "help", "message": """Available commands:
/add-student <name> - Add a new student
/grade <name> <score> [--subject <subject>] [--date YYYY-MM-DD] - Add a grade
/behavior <name> <type> [--note "note"] [--date YYYY-MM-DD] - Record behavior (positive/negative/neutral)
/attendance <name> present|absent|late [--date YYYY-MM-DD] - Mark attendance
/homework <name> <title> [--due YYYY-MM-DD] [--status <status>] - Add homework
/report <name> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--pdf] - Get student report
/dashboard <name> - Open student dashboard
/dashboard - List all students
/help - Show this help"""}
    
    return {"action": "invalid", "message": f"Unknown command: /{cmd}. Type /help for available commands."}