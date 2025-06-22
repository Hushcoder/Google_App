import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()

# === CONFIG ===
SPREADSHEET_ID = '1SGnwsvlJgoppipYm0g0cw9dU318-1mYDA5GQeYp1yZE'
RANGE = 'Form Responses 1!C:D'  # Adjust columns as needed
PROCESSED_FLAG_FILE = 'processed_ids.txt'
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

EMAIL_USER = st.secrets["EMAIL"]
EMAIL_PASS = st.secrets["APP_PASSWORD"]

# === AUTHENTICATE SHEETS ===
def get_sheet_service():
    creds = service_account.Credentials.from_service_account_info(
        dict(st.secrets["google"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return build("sheets", "v4", credentials=creds)

# === READ GOOGLE SHEET ===
def get_form_data():
    service = get_sheet_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE
    ).execute()
    values = result.get('values', [])[1:]  # skip header
    return values

# === GEMINI REPLY GENERATOR ===
def generate_reply(user_message, user_name):
    prompt = f"Write a polite and helpful email in response to the following query:\n\nName: {user_name}\nQuery: {user_message}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, json=payload)
    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text']

# === SEND EMAIL ===
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# === MAIN AUTOMATION ===
def main():
    if os.path.exists(PROCESSED_FLAG_FILE):
        with open(PROCESSED_FLAG_FILE, 'r') as f:
            processed = set(f.read().splitlines())
    else:
        processed = set()

    data = get_form_data()

    with open(PROCESSED_FLAG_FILE, 'a') as f:
        for row in data:
            if len(row) < 4:
                continue
            timestamp, name, email, message = row
            if timestamp in processed:
                continue

            reply = generate_reply(message, name)
            send_email(email, "Re: Your Query", reply)

            f.write(timestamp + '\n')
            print(f"Email sent to {email}")
