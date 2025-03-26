from flask import Flask, request, jsonify, render_template, redirect
import datetime
import smtplib
import os
import json
import base64
import gspread
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# -------------------------------------------
# Google Sheets Configuration
# -------------------------------------------
SHEET_NAME = "Machine Breakdown"  # ✅ Change this if your sheet has a different name

def authenticate_sheets():
    try:
        # Read base64 encoded credentials from Azure Environment Variables
        encoded_creds = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if not encoded_creds:
            print("❌ Missing GOOGLE_CREDENTIALS_BASE64 env variable")
            return None

        # Decode and load credentials
        creds_json = base64.b64decode(encoded_creds).decode('utf-8')
        creds_dict = json.loads(creds_json)

        # Authenticate with Google API
        creds = Credentials.from_service_account_info(creds_dict)
        creds = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        print("✅ Google Sheets Authentication Successful")

        return client.open(SHEET_NAME).sheet1

    except Exception as e:
        print("❌ Error authenticating with Google Sheets:", e)
        return None

# -------------------------------------------
# Email Configuration (Azure Safe)
# -------------------------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER")          # ✅ Setup this in Azure Configuration
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")      # ✅ Use an App Password, not your main Gmail password
EMAIL_MANAGER = "laxmi@pck-buderus.com"           # ✅ Change if needed

# -------------------------------------------
# Email Sending Function
# -------------------------------------------
def send_email_alert(machine_name):
    subject = f"ALERT: Frequent Breakdown for {machine_name}"
    body = f"The machine '{machine_name}' has encountered more than 2 breakdowns within the last week."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_MANAGER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_MANAGER, msg.as_string())
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Error sending email:", e)

# -------------------------------------------
# Routes
# -------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        sheet = authenticate_sheets()
        if not sheet:
            return jsonify({"error": "Failed to connect to Google Sheets"}), 500

        machine_name = request.form.get("machine_name")
        issue = request.form.get("issue")
        date = datetime.datetime.now().strftime("%Y-%m-%d")

        if not machine_name or not issue:
            return jsonify({"error": "Both fields are required"}), 400

        # Insert data into sheet
        sheet.append_row([date, machine_name, issue])
        print("✅ Breakdown recorded")

        # Check if the machine had more than 2 issues in the last 7 days
        recent_issues = 0
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        records = sheet.get_all_values()

        for row in records[1:]:  # skip header if present
            try:
                row_date = datetime.datetime.strptime(row[0], "%Y-%m-%d")
                if row[1] == machine_name and row_date >= one_week_ago:
                    recent_issues += 1
            except ValueError:
                continue  # skip rows with bad dates

        if recent_issues > 2:
            send_email_alert(machine_name)

        return jsonify({"message": "Breakdown recorded successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/open_log")
def open_log():
    return redirect("https://docs.google.com/spreadsheets/d/1G368ctBWJ88OAKQik3Imu-Hzu1PkrCzpYnyuuiCrmXc/edit?usp=sharing")

@app.route("/health")
def health():
    return jsonify({"status": "running"})

# -------------------------------------------
# Run App
# -------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
