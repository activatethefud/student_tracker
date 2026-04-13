from weasyprint import HTML
from datetime import datetime


def generate_pdf_report(student, grades, behaviors, attendances, homeworks, activities, avg_grade, date_range=""):
    grades_html = ""
    for g in grades:
        grades_html += f"<tr><td>{g.subject}</td><td>{g.score}</td><td>{g.created_at.strftime('%Y-%m-%d %H:%M')}</td></tr>"
    
    if not grades_html:
        grades_html = "<tr><td colspan='3'>No grades recorded</td></tr>"
    
    behaviors_html = ""
    for b in behaviors:
        behaviors_html += f"<tr><td>{b.behavior_type}</td><td>{b.note}</td><td>{b.created_at.strftime('%Y-%m-%d %H:%M')}</td></tr>"
    
    if not behaviors_html:
        behaviors_html = "<tr><td colspan='3'>No behaviors recorded</td></tr>"
    
    homework_html = ""
    pending_count = 0
    submitted_count = 0
    other_count = 0
    for h in homeworks:
        due_str = f", Due: {h.due_date.strftime('%Y-%m-%d')}" if h.due_date else ""
        homework_html += f"<tr><td>{h.title}</td><td>{h.status}</td><td>{h.created_at.strftime('%Y-%m-%d')}{due_str}</td></tr>"
        if h.status.lower() == "pending":
            pending_count += 1
        elif h.status.lower() == "submitted":
            submitted_count += 1
        else:
            other_count += 1
    
    if not homework_html:
        homework_html = "<tr><td colspan='3'>No homework assigned</td></tr>"
    
    taking_notes_yes = len([a for a in activities if a.activity_type == "taking-notes" and a.status == "yes"])
    taking_notes_no = len([a for a in activities if a.activity_type == "taking-notes" and a.status == "no"])
    participation_yes = len([a for a in activities if a.activity_type == "participation" and a.status == "yes"])
    participation_no = len([a for a in activities if a.activity_type == "participation" and a.status == "no"])
    
    activity_html = ""
    for a in activities:
        activity_html += f"<tr><td>{a.activity_type}</td><td>{a.status}</td><td>{a.date.strftime('%Y-%m-%d')}</td></tr>"
    
    if not activity_html:
        activity_html = "<tr><td colspan='3'>No activity records</td></tr>"
    
    present = len([a for a in attendances if a.status == 'present'])
    absent = len([a for a in attendances if a.status == 'absent'])
    late = len([a for a in attendances if a.status == 'late'])
    total = present + absent + late
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Student Report - {student.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f5f5f5; }}
            .summary {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .summary-item {{ margin: 10px 0; }}
            .label {{ font-weight: bold; }}
            .footer {{ margin-top: 40px; font-size: 12px; color: #888; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>Student Report: {student.name}</h1>
        <p><strong>Student ID:</strong> {student.student_id or 'N/A'} | <strong>Year:</strong> {student.year or 'N/A'}</p>
        {f'<p><em>Report Period: {date_range}</em></p>' if date_range else ''}
        
        <div class="summary">
            <div class="summary-item"><span class="label">Average Grade:</span> {avg_grade:.2f}</div>
            <div class="summary-item"><span class="label">Total Grades:</span> {len(grades)}</div>
            <div class="summary-item"><span class="label">Total Behaviors:</span> {len(behaviors)}</div>
            <div class="summary-item"><span class="label">Attendance:</span> {present} present, {absent} absent, {late} late (out of {total})</div>
            <div class="summary-item"><span class="label">Homework:</span> {pending_count} pending, {submitted_count} submitted, {other_count} other (out of {len(homeworks)})</div>
            <div class="summary-item"><span class="label">Activity - Taking Notes:</span> {taking_notes_yes} yes, {taking_notes_no} no</div>
            <div class="summary-item"><span class="label">Activity - Participation:</span> {participation_yes} yes, {participation_no} no</div>
            {f'<div class="summary-item"><span class="label">Details:</span> {student.details}</div>' if student.details else ''}
        </div>
        
        <h2>Grades</h2>
        <table>
            <thead><tr><th>Subject</th><th>Score</th><th>Date</th></tr></thead>
            <tbody>{grades_html}</tbody>
        </table>
        
        <h2>Behaviors</h2>
        <table>
            <thead><tr><th>Type</th><th>Note</th><th>Date</th></tr></thead>
            <tbody>{behaviors_html}</tbody>
        </table>
        
        <h2>Attendance</h2>
        <table>
            <thead><tr><th>Status</th><th>Date</th></tr></thead>
            <tbody>
                {''.join(f"<tr><td>{a.status}</td><td>{a.date.strftime('%Y-%m-%d')}</td></tr>" for a in attendances) if attendances else '<tr><td colspan="2">No attendance records</td></tr>'}
            </tbody>
        </table>
        
        <h2>Homework</h2>
        <table>
            <thead><tr><th>Title</th><th>Status</th><th>Assigned/Due</th></tr></thead>
            <tbody>{homework_html}</tbody>
        </table>
        
        <h2>Activity</h2>
        <table>
            <thead><tr><th>Type</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>{activity_html}</tbody>
        </table>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by Student Tracker
        </div>
    </body>
    </html>
    """
    
    return HTML(string=html).write_pdf()