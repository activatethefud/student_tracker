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
            return {"action": "error", "message": "Usage: /grade <name> <score> [--subject Math]"}
        name = args[0]
        try:
            score = float(args[1])
        except ValueError:
            return {"action": "error", "message": "Score must be a number"}
        subject = "General"
        for i, arg in enumerate(args):
            if arg == "--subject" and i + 1 < len(args):
                subject = args[i + 1]
                break
        return {"action": "add_grade", "student_name": name, "score": score, "subject": subject}
    
    if cmd in ("behavior", "behave"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /behavior <name> <type> [--note \"text\"]"}
        name = args[0]
        behavior_type = "neutral"
        note = ""
        for i, arg in enumerate(args):
            if arg == "--note" and i + 1 < len(args):
                note = " ".join(args[i+1:]).strip('"')
                break
            elif arg in ("positive", "negative", "neutral"):
                behavior_type = arg
        return {"action": "add_behavior", "student_name": name, "behavior_type": behavior_type, "note": note}
    
    if cmd in ("attendance", "attend"):
        if len(args) < 2:
            return {"action": "error", "message": "Usage: /attendance <name> present|absent|late"}
        return {"action": "mark_attendance", "student_name": args[0], "status": args[1].lower()}
    
    if cmd in ("report", "stats"):
        if len(args) < 1:
            return {"action": "error", "message": "Usage: /report <name>"}
        return {"action": "get_report", "student_name": args[0]}
    
    if cmd == "help":
        return {"action": "help", "message": """Available commands:
/add-student <name> - Add a new student
/grade <name> <score> [--subject <subject>] - Add a grade
/behavior <name> <type> [--note "note"] - Record behavior (positive/negative/neutral)
/attendance <name> present|absent|late - Mark attendance
/report <name> - Get student report
/help - Show this help"""}
    
    return {"action": "invalid", "message": f"Unknown command: /{cmd}. Type /help for available commands."}