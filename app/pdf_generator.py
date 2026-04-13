from weasyprint import HTML
from datetime import datetime
import pygal
from pygal.style import Style


def _make_chart_svg(chart):
    return chart.render(disable_xml_declaration=True)


def _grade_color(score):
    if score >= 90:
        return "#16a34a"
    if score >= 80:
        return "#2563eb"
    if score >= 70:
        return "#d97706"
    if score >= 60:
        return "#ea580c"
    return "#dc2626"


def _attendance_donut(attendances):
    present = len([a for a in attendances if a.status == "present"])
    absent = len([a for a in attendances if a.status == "absent"])
    late = len([a for a in attendances if a.status == "late"])
    if present + absent + late == 0:
        return ""
    style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#333",
        foreground_light="#333",
        foreground_dark="#333",
        opacity=".8",
        opacity_hover=".9",
        transition="200ms ease-in",
        colors=("#16a34a", "#dc2626", "#d97706"),
    )
    chart = pygal.Pie(style=style, inner_radius=0.5, width=200, height=200, show_legend=True)
    chart.title = "Attendance"
    if present:
        chart.add("Present", present)
    if absent:
        chart.add("Absent", absent)
    if late:
        chart.add("Late", late)
    return _make_chart_svg(chart)


def _behavior_bar(behaviors):
    if not behaviors:
        return ""
    positive = len([b for b in behaviors if b.behavior_type == "positive"])
    negative = len([b for b in behaviors if b.behavior_type == "negative"])
    neutral = len([b for b in behaviors if b.behavior_type == "neutral"])
    style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#333",
        foreground_light="#333",
        foreground_dark="#333",
        opacity=".8",
        colors=("#16a34a", "#dc2626", "#9ca3af"),
    )
    chart = pygal.Bar(style=style, width=240, height=200, show_legend=True)
    chart.title = "Behavior"
    chart.add("Positive", positive)
    chart.add("Negative", negative)
    chart.add("Neutral", neutral)
    chart.x_labels = ["Positive", "Negative", "Neutral"]
    return _make_chart_svg(chart)


def _grades_by_subject_bar(grades):
    if not grades:
        return ""
    subjects = {}
    for g in grades:
        if g.subject not in subjects:
            subjects[g.subject] = []
        subjects[g.subject].append(g.score)
    avg_by_subject = {s: sum(v) / len(v) for s, v in subjects.items()}
    style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#333",
        foreground_light="#333",
        foreground_dark="#333",
        opacity=".8",
        colors=("#2563eb",),
    )
    chart = pygal.Bar(style=style, width=300, height=200, show_legend=False)
    chart.title = "Average by Subject"
    for s, avg in avg_by_subject.items():
        chart.add(s, round(avg, 1))
    chart.x_labels = list(avg_by_subject.keys())
    return _make_chart_svg(chart)


def _activity_bar(activities):
    if not activities:
        return ""
    activity_types = sorted(set(a.activity_type for a in activities))
    style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#333",
        foreground_light="#333",
        foreground_dark="#333",
        opacity=".8",
        colors=("#16a34a", "#dc2626"),
    )
    chart = pygal.Bar(style=style, width=300, height=200, show_legend=True)
    chart.title = "Activity"
    yes_data = []
    no_data = []
    for atype in activity_types:
        yes_data.append(len([a for a in activities if a.activity_type == atype and a.status == "yes"]))
        no_data.append(len([a for a in activities if a.activity_type == atype and a.status == "no"]))
    chart.add("Yes", yes_data)
    chart.add("No", no_data)
    chart.x_labels = activity_types
    return _make_chart_svg(chart)


def generate_pdf_report(student, grades, behaviors, attendances, homeworks, activities, avg_grade, date_range=""):
    avg_grade_val = avg_grade if avg_grade else 0
    present = len([a for a in attendances if a.status == "present"])
    absent = len([a for a in attendances if a.status == "absent"])
    late = len([a for a in attendances if a.status == "late"])
    total_attendance = present + absent + late
    attendance_pct = round((present / total_attendance) * 100, 1) if total_attendance > 0 else 0
    pending_hw = len([h for h in homeworks if h.status.lower() == "pending"])
    submitted_hw = len([h for h in homeworks if h.status.lower() == "submitted"])
    positive_behaviors = len([b for b in behaviors if b.behavior_type == "positive"])
    total_behaviors = len(behaviors)
    behavior_pct = round((positive_behaviors / total_behaviors) * 100, 1) if total_behaviors > 0 else 0

    charts_css = ""
    attendance_chart = _attendance_donut(attendances)
    behavior_chart = _behavior_bar(behaviors)
    grades_chart = _grades_by_subject_bar(grades)
    activity_chart = _activity_bar(activities)

    charts_row = ""
    chart_parts = []
    if attendance_chart:
        chart_parts.append(f'<div class="chart-card">{attendance_chart}</div>')
    if behavior_chart:
        chart_parts.append(f'<div class="chart-card">{behavior_chart}</div>')
    if grades_chart:
        chart_parts.append(f'<div class="chart-card">{grades_chart}</div>')
    if activity_chart:
        chart_parts.append(f'<div class="chart-card">{activity_chart}</div>')
    if chart_parts:
        charts_row = f'<div class="charts-row">{"".join(chart_parts)}</div>'

    grades_rows = ""
    if grades:
        for g in sorted(grades, key=lambda x: x.created_at, reverse=True):
            color = _grade_color(g.score)
            grade_label = "A" if g.score >= 90 else "B" if g.score >= 80 else "C" if g.score >= 70 else "D" if g.score >= 60 else "F"
            grades_rows += f"""
            <div class="record-card">
                <div class="record-main">
                    <span class="grade-badge" style="background:{color}">{grade_label}</span>
                    <div class="record-info">
                        <strong>{g.subject}</strong>
                        <span class="record-date">{g.created_at.strftime('%Y-%m-%d')}</span>
                    </div>
                </div>
                <div class="record-score" style="color:{color}">{g.score:.0f}%</div>
            </div>"""
    else:
        grades_rows = '<p class="empty-msg">No grades recorded</p>'

    behavior_rows = ""
    if behaviors:
        for b in sorted(behaviors, key=lambda x: x.created_at, reverse=True):
            color = "#16a34a" if b.behavior_type == "positive" else "#dc2626" if b.behavior_type == "negative" else "#9ca3af"
            behavior_rows += f"""
            <div class="record-card">
                <span class="pill" style="background:{color}; color:white">{b.behavior_type}</span>
                <span class="record-note">{b.note or ''}</span>
                <span class="record-date">{b.created_at.strftime('%Y-%m-%d')}</span>
            </div>"""
    else:
        behavior_rows = '<p class="empty-msg">No behaviors recorded</p>'

    attendance_rows = ""
    if attendances:
        for a in sorted(attendances, key=lambda x: x.date, reverse=True):
            color = "#16a34a" if a.status == "present" else "#dc2626" if a.status == "absent" else "#d97706"
            attendance_rows += f"""
            <div class="record-card">
                <span class="pill" style="background:{color}; color:white">{a.status}</span>
                <span class="record-date">{a.date.strftime('%Y-%m-%d')}</span>
            </div>"""
    else:
        attendance_rows = '<p class="empty-msg">No attendance records</p>'

    homework_rows = ""
    if homeworks:
        for h in sorted(homeworks, key=lambda x: x.created_at, reverse=True):
            color = "#d97706" if h.status.lower() == "pending" else "#16a34a" if h.status.lower() == "submitted" else "#6b7280"
            due_str = f" &middot; Due {h.due_date.strftime('%Y-%m-%d')}" if h.due_date else ""
            homework_rows += f"""
            <div class="record-card">
                <span class="pill" style="background:{color}; color:white">{h.status}</span>
                <span class="record-note">{h.title}{due_str}</span>
                <span class="record-date">{h.created_at.strftime('%Y-%m-%d')}</span>
            </div>"""
    else:
        homework_rows = '<p class="empty-msg">No homework assigned</p>'

    activity_rows = ""
    if activities:
        activity_types = sorted(set(a.activity_type for a in activities))
        for atype in activity_types:
            atype_activities = sorted(
                [a for a in activities if a.activity_type == atype],
                key=lambda x: x.date, reverse=True
            )
            activity_rows += f'<div class="activity-group"><strong>{atype}</strong></div>'
            for a in atype_activities:
                color = "#16a34a" if a.status == "yes" else "#dc2626"
                label = "Yes" if a.status == "yes" else "No"
                activity_rows += f"""
                <div class="record-card">
                    <span class="pill" style="background:{color}; color:white">{label}</span>
                    <span class="record-date">{a.date.strftime('%Y-%m-%d')}</span>
                </div>"""
    else:
        activity_rows = '<p class="empty-msg">No activity records</p>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Student Report - {student.name}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background: #f9fafb; color: #1f2937; line-height: 1.6; padding: 40px; }}
            .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 32px 40px; border-radius: 12px; margin-bottom: 24px; }}
            .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
            .header .meta {{ font-size: 14px; opacity: 0.85; }}
            .header .meta span {{ margin-right: 16px; }}
            .summary-row {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
            .summary-card {{ flex: 1; min-width: 140px; background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
            .summary-card .value {{ font-size: 32px; font-weight: 700; }}
            .summary-card .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}
            .card-blue .value {{ color: #2563eb; }}
            .card-green .value {{ color: #16a34a; }}
            .card-yellow .value {{ color: #d97706; }}
            .card-purple .value {{ color: #7c3aed; }}
            .charts-row {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
            .chart-card {{ background: white; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); flex: 1; min-width: 200px; }}
            .section {{ background: white; border-radius: 10px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
            .section h2 {{ font-size: 18px; font-weight: 600; color: #374151; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
            .record-card {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }}
            .record-card:last-child {{ border-bottom: none; }}
            .record-main {{ display: flex; align-items: center; gap: 12px; }}
            .record-info {{ display: flex; flex-direction: column; }}
            .record-score {{ font-size: 20px; font-weight: 700; }}
            .record-date {{ font-size: 12px; color: #9ca3af; }}
            .record-note {{ color: #4b5563; font-size: 14px; flex: 1; }}
            .grade-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 8px; color: white; font-weight: 700; font-size: 16px; }}
            .pill {{ display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin-right: 8px; }}
            .empty-msg {{ color: #9ca3af; text-align: center; padding: 16px; font-size: 14px; }}
            .activity-group {{ font-size: 14px; color: #6b7280; padding: 8px 0 4px 0; border-top: 1px solid #e5e7eb; margin-top: 8px; }}
            .activity-group:first-child {{ border-top: none; margin-top: 0; }}
            .footer {{ text-align: center; font-size: 11px; color: #9ca3af; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
            svg {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{student.name}</h1>
            <div class="meta">
                {"<span>ID: " + student.student_id + "</span>" if student.student_id else ""}
                {"<span>Year: " + student.year + "</span>" if student.year else ""}
                {"<span>Report Period: " + date_range + "</span>" if date_range else ""}
            </div>
            {"<div class='meta' style='margin-top:8px;opacity:0.9'>" + student.details + "</div>" if student.details else ""}
        </div>

        <div class="summary-row">
            <div class="summary-card card-blue">
                <div class="value">{avg_grade_val:.1f}%</div>
                <div class="label">Average Grade</div>
            </div>
            <div class="summary-card card-green">
                <div class="value">{attendance_pct}%</div>
                <div class="label">Attendance Rate</div>
            </div>
            <div class="summary-card card-yellow">
                <div class="value">{pending_hw}</div>
                <div class="label">Pending HW</div>
            </div>
            <div class="summary-card card-purple">
                <div class="value">{behavior_pct}%</div>
                <div class="label">Positive Behavior</div>
            </div>
        </div>

        {charts_row}

        <div class="section">
            <h2>Grades</h2>
            {grades_rows}
        </div>

        <div class="section">
            <h2>Behavior</h2>
            {behavior_rows}
        </div>

        <div class="section">
            <h2>Attendance</h2>
            {attendance_rows}
        </div>

        <div class="section">
            <h2>Homework</h2>
            {homework_rows}
        </div>

        <div class="section">
            <h2>Activity</h2>
            {activity_rows}
        </div>

        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by Student Tracker
        </div>
    </body>
    </html>
    """

    return HTML(string=html).write_pdf()