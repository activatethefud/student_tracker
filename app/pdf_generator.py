from weasyprint import HTML
from datetime import datetime


def _grade_color(score):
    if score >= 5:
        return "#16a34a"
    if score >= 4:
        return "#2563eb"
    if score >= 3:
        return "#d97706"
    if score >= 2:
        return "#ea580c"
    return "#dc2626"


def _behavior_color(behavior_type):
    if behavior_type == "positive":
        return "#16a34a"
    if behavior_type == "negative":
        return "#dc2626"
    return "#9ca3af"


def _attendance_donut_html(attendances):
    present = len([a for a in attendances if a.status == "present"])
    absent = len([a for a in attendances if a.status == "absent"])
    late = len([a for a in attendances if a.status == "late"])
    total = present + absent + late
    if total == 0:
        return ""
    pct = round((present + late * 0.5) / total * 100, 1)
    present_deg = round(present / total * 360, 1)
    late_deg = round(late / total * 360, 1)
    green_end = present_deg
    yellow_end = green_end + late_deg
    conic = f"conic-gradient(#16a34a 0deg {green_end}deg, #d97706 {green_end}deg {yellow_end}deg, #dc2626 {yellow_end}deg 360deg)"
    return f"""
    <div class="css-chart">
        <h3>Attendance</h3>
        <div class="donut-ring" style="background: {conic}">
            <div class="donut-inner">
                <div class="donut-pct">{pct}%</div>
                <div class="donut-sub">{present}/{total}</div>
            </div>
        </div>
        <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background:#16a34a"></span>Present {present}</span>
            <span class="legend-item"><span class="legend-dot" style="background:#d97706"></span>Late {late}</span>
            <span class="legend-item"><span class="legend-dot" style="background:#dc2626"></span>Absent {absent}</span>
        </div>
    </div>"""


def _grades_by_subject_html(grades):
    if not grades:
        return ""
    subjects = {}
    for g in grades:
        if g.subject not in subjects:
            subjects[g.subject] = []
        subjects[g.subject].append(g.score)
    rows = ""
    for subject, scores in sorted(subjects.items()):
        avg = sum(scores) / len(scores)
        pct = min(avg / 5 * 100, 100)
        color = _grade_color(avg)
        rows += f"""
        <div class="bar-row">
            <div class="bar-label">{subject}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width:{pct:.0f}%; background:{color}"></div>
            </div>
            <div class="bar-value" style="color:{color}">{avg:.1f}</div>
        </div>"""
    return f"""
    <div class="css-chart">
        <h3>Grades by Subject</h3>
        {rows}
    </div>"""


def _behavior_bar_html(behaviors):
    if not behaviors:
        return ""
    positive = len([b for b in behaviors if b.behavior_type == "positive"])
    negative = len([b for b in behaviors if b.behavior_type == "negative"])
    neutral = len([b for b in behaviors if b.behavior_type == "neutral"])
    total = len(behaviors)
    p_pct = round(positive / total * 100, 1) if total else 0
    n_pct = round(negative / total * 100, 1) if total else 0
    nu_pct = 100 - p_pct - n_pct if total else 0
    return f"""
    <div class="css-chart">
        <h3>Behavior</h3>
        <div class="stacked-bar">
            <div class="stacked-segment" style="width:{p_pct:.1f}%; background:#16a34a; border-radius: 6px 0 0 6px"></div>
            <div class="stacked-segment" style="width:{nu_pct:.1f}%; background:#9ca3af"></div>
            <div class="stacked-segment" style="width:{n_pct:.1f}%; background:#dc2626; border-radius: 0 6px 6px 0"></div>
        </div>
        <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background:#16a34a"></span>Positive {positive}</span>
            <span class="legend-item"><span class="legend-dot" style="background:#9ca3af"></span>Neutral {neutral}</span>
            <span class="legend-item"><span class="legend-dot" style="background:#dc2626"></span>Negative {negative}</span>
        </div>
    </div>"""


def _activity_bars_html(activities):
    if not activities:
        return ""
    activity_types = sorted(set(a.activity_type for a in activities))
    rows = ""
    for atype in activity_types:
        atype_acts = [a for a in activities if a.activity_type == atype]
        yes_count = len([a for a in atype_acts if a.status == "yes"])
        no_count = len([a for a in atype_acts if a.status == "no"])
        total = len(atype_acts)
        yes_pct = round(yes_count / total * 100, 1) if total else 0
        no_pct = 100 - yes_pct if total else 0
        rows += f"""
        <div class="bar-row">
            <div class="bar-label">{atype}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width:{yes_pct:.0f}%; background:#16a34a; border-radius:6px 0 0 6px"></div>
                <div class="bar-fill-negative" style="width:{no_pct:.0f}%; background:#dc2626; border-radius:0 6px 6px 0"></div>
            </div>
            <div class="bar-value" style="color:#16a34a">{yes_count}<span style="color:#9ca3af;font-weight:400">/{total}</span></div>
        </div>"""
    return f"""
    <div class="css-chart">
        <h3>Activity</h3>
        {rows}
    </div>"""


def _progress_chart_html(progresses):
    if not progresses:
        return ""
    progress_goals = sorted(set(p.goal for p in progresses))
    rows = ""
    for goal in progress_goals:
        goal_entries = sorted([p for p in progresses if p.goal == goal], key=lambda x: x.date)
        latest = goal_entries[-1]
        values = [p.value for p in goal_entries]
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        rows += f"""
        <div class="bar-row">
            <div class="bar-label">{goal}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width:{min(max_val / (max_val * 1.2 if max_val > 0 else 1) * 100, 100):.0f}%; background:#7c3aed; border-radius:6px"></div>
            </div>
            <div class="bar-value" style="color:#7c3aed">{latest.value:.1f}</div>
        </div>"""
    return f"""
    <div class="css-chart">
        <h3>Progress</h3>
        {rows}
    </div>"""


def generate_pdf_report(student, grades, behaviors, attendances, homeworks, activities, progresses, avg_grade, date_range=""):
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

    charts_html = ""
    chart_parts = []
    att_chart = _attendance_donut_html(attendances)
    if att_chart:
        chart_parts.append(att_chart)
    grade_chart = _grades_by_subject_html(grades)
    if grade_chart:
        chart_parts.append(grade_chart)
    beh_chart = _behavior_bar_html(behaviors)
    if beh_chart:
        chart_parts.append(beh_chart)
    act_chart = _activity_bars_html(activities)
    if act_chart:
        chart_parts.append(act_chart)
    prog_chart = _progress_chart_html(progresses)
    if prog_chart:
        chart_parts.append(prog_chart)
    if chart_parts:
        charts_html = f'<div class="charts-row">{"".join(chart_parts)}</div>'

    grades_rows = ""
    if grades:
        for g in sorted(grades, key=lambda x: x.created_at, reverse=True):
            color = _grade_color(g.score)
            grades_rows += f"""
            <div class="record-card">
                <div class="record-main">
                    <span class="grade-badge" style="background:{color}">{g.score:.0f}</span>
                    <div class="record-info">
                        <strong>{g.subject}</strong>
                        <span class="record-date">{g.created_at.strftime('%Y-%m-%d')}</span>
                    </div>
                </div>
            </div>"""
    else:
        grades_rows = '<p class="empty-msg">No grades recorded</p>'

    behavior_rows = ""
    if behaviors:
        for b in sorted(behaviors, key=lambda x: x.created_at, reverse=True):
            color = _behavior_color(b.behavior_type)
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

    progress_rows = ""
    if progresses:
        progress_goals = sorted(set(p.goal for p in progresses))
        for goal in progress_goals:
            goal_entries = sorted(
                [p for p in progresses if p.goal == goal],
                key=lambda x: x.date, reverse=True
            )
            progress_rows += f'<div class="activity-group"><strong>{goal}</strong></div>'
            for p in goal_entries:
                progress_rows += f"""
                <div class="record-card">
                    <span class="pill" style="background:#7c3aed; color:white">{p.value:.1f}</span>
                    <span class="record-date">{p.date.strftime('%Y-%m-%d')}</span>
                </div>"""
    else:
        progress_rows = '<p class="empty-msg">No progress records</p>'

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
            .css-chart {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); flex: 1; min-width: 240px; }}
            .css-chart h3 {{ font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 12px; }}
            .donut-ring {{ width: 120px; height: 120px; border-radius: 50%; margin: 0 auto 12px; position: relative; }}
            .donut-inner {{ position: absolute; top: 12px; left: 12px; right: 12px; bottom: 12px; background: white; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
            .donut-pct {{ font-size: 22px; font-weight: 700; color: #1f2937; }}
            .donut-sub {{ font-size: 11px; color: #6b7280; }}
            .chart-legend {{ display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; font-size: 12px; color: #4b5563; }}
            .legend-item {{ display: flex; align-items: center; gap: 4px; }}
            .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
            .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
            .bar-label {{ width: 80px; font-size: 13px; color: #4b5563; text-align: right; flex-shrink: 0; }}
            .bar-track {{ flex: 1; height: 20px; background: #e5e7eb; border-radius: 6px; overflow: hidden; position: relative; }}
            .bar-fill {{ height: 100%; border-radius: 6px; transition: width 0.3s; }}
            .bar-fill-negative {{ height: 100%; position: absolute; top: 0; right: 0; border-radius: 0 6px 6px 0; }}
            .bar-value {{ width: 32px; font-size: 14px; font-weight: 700; flex-shrink: 0; }}
            .stacked-bar {{ display: flex; height: 24px; border-radius: 6px; overflow: hidden; margin-bottom: 8px; }}
            .stacked-segment {{ height: 100%; }}
            .section {{ background: white; border-radius: 10px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
            .section h2 {{ font-size: 18px; font-weight: 600; color: #374151; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }}
            .record-card {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }}
            .record-card:last-child {{ border-bottom: none; }}
            .record-main {{ display: flex; align-items: center; gap: 12px; }}
            .record-info {{ display: flex; flex-direction: column; }}
            .record-date {{ font-size: 12px; color: #9ca3af; }}
            .record-note {{ color: #4b5563; font-size: 14px; flex: 1; }}
            .grade-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 8px; color: white; font-weight: 700; font-size: 16px; }}
            .pill {{ display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin-right: 8px; }}
            .empty-msg {{ color: #9ca3af; text-align: center; padding: 16px; font-size: 14px; }}
            .activity-group {{ font-size: 14px; color: #6b7280; padding: 8px 0 4px 0; border-top: 1px solid #e5e7eb; margin-top: 8px; }}
            .activity-group:first-child {{ border-top: none; margin-top: 0; }}
            .footer {{ text-align: center; font-size: 11px; color: #9ca3af; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
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
            {f'<div class="summary-card card-blue"><div class="value">{avg_grade_val:.1f}</div><div class="label">Average Grade</div></div>' if grades else ''}
            {f'<div class="summary-card card-green"><div class="value">{attendance_pct}%</div><div class="label">Attendance Rate</div></div>' if total_attendance > 0 else ''}
            {f'<div class="summary-card card-yellow"><div class="value">{pending_hw}</div><div class="label">Pending HW</div></div>' if homeworks else ''}
            {f'<div class="summary-card card-purple"><div class="value">{behavior_pct}%</div><div class="label">Positive Behavior</div></div>' if total_behaviors > 0 else ''}
        </div>

        {charts_html}

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

        {f'<div class="section"><h2>Progress</h2>{progress_rows}</div>' if progresses else ''}

        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by Student Tracker
        </div>
    </body>
    </html>
    """

    return HTML(string=html).write_pdf()