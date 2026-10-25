"""
Absentee Notification Generator
Generates automated parent/student notices for absent students (WhatsApp, SMS, Email)
"""

import os
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_absentee_messages(
    absent_students: List[Dict],
    date: str,
    subject: str = "General",
    session: str = "Morning",
    institution_name: str = "Classroom Attendance Studio"
) -> List[Dict]:
    """
    Generate personalized notice texts for each absent student.
    Returns list of dicts with student details and ready-to-dispatch messages.
    """
    notices = []
    formatted_date = date

    for s in absent_students:
        name = s.get("name") or s.get("Name", "Student")
        roll = s.get("roll_no") or s.get("Roll No", "--")
        prn = s.get("prn") or s.get("PRN", "--")
        phone = s.get("phone", "")

        # 1. WhatsApp Text
        whatsapp_text = (
            f"📢 *Attendance Notice — {institution_name}*\n\n"
            f"Dear Parent / Student,\n"
            f"This is an automated notification to inform you that *{name}* "
            f"(Roll No: *{roll}*, PRN: *{prn}*) was marked *ABSENT* for:\n"
            f"• *Subject:* {subject}\n"
            f"• *Date:* {formatted_date}\n"
            f"• *Session:* {session}\n\n"
            f"If you have medical leave or an official excuse, please submit documentation to the faculty."
        )

        # 2. SMS Short Text (<= 160 chars)
        sms_text = (
            f"ATTENDANCE NOTICE: {name} (Roll {roll}) was marked ABSENT for "
            f"{subject} on {formatted_date} ({session}). Contact faculty for queries."
        )

        # 3. Email Body
        email_subject = f"Attendance Notice: {name} ({roll}) Absent for {subject} on {formatted_date}"
        email_body = (
            f"Dear Parent / Guardian,\n\n"
            f"This is an automated notice regarding the attendance record of {name}.\n\n"
            f"Student Details:\n"
            f"- Name: {name}\n"
            f"- Roll Number: {roll}\n"
            f"- PRN: {prn}\n\n"
            f"Attendance Status:\n"
            f"- Date: {formatted_date}\n"
            f"- Session: {session}\n"
            f"- Subject: {subject}\n"
            f"- Status: ABSENT\n\n"
            f"Please ensure regular attendance to maintain the required minimum threshold (75%).\n\n"
            f"Regards,\n"
            f"{institution_name}"
        )

        encoded_wa = urllib.parse.quote(whatsapp_text)
        wa_url = f"https://api.whatsapp.com/send?text={encoded_wa}"
        if phone:
            wa_url = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_wa}"

        notices.append({
            "name": name,
            "roll_no": roll,
            "prn": prn,
            "phone": phone,
            "subject": subject,
            "date": formatted_date,
            "session": session,
            "whatsapp_text": whatsapp_text,
            "whatsapp_url": wa_url,
            "sms_text": sms_text,
            "email_subject": email_subject,
            "email_body": email_body,
        })

    return notices


def export_absentee_dispatch_csv(notices: List[Dict], filepath: str) -> str:
    """Export the list of absentee alerts as a CSV dispatch sheet."""
    import pandas as pd
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df = pd.DataFrame(notices)
    df.to_csv(filepath, index=False)
    return filepath
