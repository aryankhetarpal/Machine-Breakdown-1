from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient
import openpyxl
import os
import smtplib
from flask import send_file
import datetime
import subprocess
from email.mime.text import MIMEText

app = Flask(__name__)

# Define Excel file
EXCEL_FILE = os.path.join(os.getcwd(), "machine_breakdowns.xlsx")


# Ensure the Excel file exists with headers
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Breakdowns"
    ws.append(["Date", "Machine Name", "Issue"])
    wb.save(EXCEL_FILE)

# Email configuration (Change these to your details)
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
        machine_name = request.form.get("machine_name")
        issue = request.form.get("issue")
        date = datetime.datetime.now().strftime("%Y-%m-%d")

        if not machine_name or not issue:
            return jsonify({"error": "Both fields are required"}), 400

        # Save data to Excel
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active
        ws.append([date, machine_name, issue])
        wb.save(EXCEL_FILE)

        # Check if the machine has more than 2 issues in a week
        recent_issues = 0
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

        for row in ws.iter_rows(values_only=True):
            if row[0] and row[1]:  # Ensure row has valid data
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

# Route to open Excel file
@app.route("/open_log")
def open_log():
    try:
        if os.path.exists(EXCEL_FILE):
            if os.name == "nt":  # Windows
                os.startfile(EXCEL_FILE)
            elif os.name == "posix":  # Mac/Linux
                subprocess.run(["open", EXCEL_FILE])
            return jsonify({"message": "Log file opened successfully!"})
        else:
            return jsonify({"error": "Log file not found!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
