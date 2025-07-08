from flask import Flask, render_template, request, redirect, flash
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = '11'

# Gmail config
EMAIL_ADDRESS = 'aryankhetarpal123@gmail.com'
EMAIL_PASSWORD = 'Aryank@123'
MANAGER_EMAIL = 'aryankhetarpal393@gmail.com'

# Google Sheets config
SPREADSHEET_ID = '1G368ctBWJ88OAKQik3Imu-Hzu1PkrCzpYnyuuiCrmXc'
RANGE_NAME = 'Sheet1!A:D'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'client_secret.json'

def get_sheet_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def log_breakdown(machine_name, issue):
    sheets = get_sheet_service()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheets.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption='RAW',
        body={'values': [[now, machine_name, issue]]}
    ).execute()

def count_issues(machine_name):
    sheets = get_sheet_service()
    result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    rows = result.get('values', [])
    count = 0
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    for row in rows:
        if len(row) >= 2:
            timestamp_str, m_name = row[0], row[1]
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            if m_name == machine_name and timestamp >= one_week_ago:
                count += 1
    return count

def send_email(machine_name, count):
    subject = f"Alert: {machine_name} has {count} issues this week"
    body = f"The machine {machine_name} has been reported broken down {count} times this week. Please investigate."

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = MANAGER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        machine_name = request.form['machine_name'].strip()
        issue = request.form['issue'].strip()

        if not machine_name or not issue:
            flash('Please fill out both fields.', 'error')
            return redirect('/')

        try:
            log_breakdown(machine_name, issue)
            count = count_issues(machine_name)
            if count > 2:
                send_email(machine_name, count)
            flash('Breakdown reported successfully.', 'success')
        except Exception as e:
            print(e)
            flash('An error occurred. Please try again.', 'error')

        return redirect('/')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
