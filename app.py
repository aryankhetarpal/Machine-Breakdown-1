from flask import Flask, request, jsonify, render_template, redirect
import datetime
import smtplib
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets configuration
SHEET_NAME = "Machine Breakdown"
CREDENTIALS_FILE = "google_credentials.json"  # Replace with your credentials file

# Authenticate with Google Sheets
def authenticate_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# Email configuration (Update these with your details)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-email-password"
EMAIL_MANAGER = "laxmi@pck-buderus.com"

# Function to send an email alert
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
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)

# Route for main form page
@app.route("/")
def index():
    return render_template("index.html")

# Handle form submission
@app.route("/submit", methods=["POST"])
def submit():
    try:
        sheet = authenticate_sheets()
        machine_name = request.form.get("machine_name")
        issue = request.form.get("issue")
        date = datetime.datetime.now().strftime("%Y-%m-%d")

        if not machine_name or not issue:
            return jsonify({"error": "Both fields are required"}), 400

        # Append data to Google Sheet
        sheet.append_row([date, machine_name, issue])
        
        # Check if the machine has more than 2 issues in a week
        recent_issues = 0
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        records = sheet.get_all_values()

        for row in records[1:]:  # Skip header row
            try:
                row_date = datetime.datetime.strptime(row[0], "%Y-%m-%d")
                if row[1] == machine_name and row_date >= one_week_ago:
                    recent_issues += 1
            except ValueError:
                continue  # Skip invalid date formats

        if recent_issues > 2:
            send_email_alert(machine_name)

        return jsonify({"message": "Breakdown recorded successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to open Google Sheet
@app.route("/open_log")
def open_log():
    return redirect("https://docs.google.com/spreadsheets/d/1G368ctBWJ88OAKQik3Imu-Hzu1PkrCzpYnyuuiCrmXc/edit?usp=sharing")  # Replace with actual sheet URL

if __name__ == "__main__":
    app.run(debug=True)
