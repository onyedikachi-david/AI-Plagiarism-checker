import os
import requests
import sqlite3
import PyPDF2
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import uuid
import threading

app = Flask(__name__)

# Configure the Flask app for session support
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create a connection to the SQLite database
conn = threading.local()

def get_db():
    if not hasattr(conn, 'db'):
        conn.db = sqlite3.connect("database.db")
        conn.db.row_factory = sqlite3.Row
    return conn.db

def close_db(error):
    if hasattr(conn, 'db'):
        conn.db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            project_title TEXT,
            plagiarism_percentage REAL,
            originality_percentage REAL
        )
        """
    )
    db.commit()

def confidenceToPercent(original, plagiarism):
    return plagiarism * 100, original * 100

def grading(original, plagiarism):
    p, o = confidenceToPercent(original, plagiarism)
    return p, o

@app.before_request
def before_first_request():
    init_db()

@app.route("/")
def home():
    # Render the home page HTML template
    return render_template("index.html")

@app.route("/check_plagiarism", methods=["POST"])
def check_plagiarism():
    # Handle the form submission for plagiarism check
    student_name = request.form.get("student-name")
    project_title = request.form.get("project-title")
    project_file = request.files.get("project-file")

    # Save the project file to the server
    file_path = save_file(project_file)

    # Extract text from the PDF file
    project_text = extract_text_from_pdf(file_path)

    # Perform plagiarism check using the extracted text
    response = requests.post(
        "https://jpwahle-plagiarism-detection.hf.space/run/predict",
        json={
            "data": [project_text]
        },
    ).json()

    data = response["data"]
    original_confidence = data[0]["confidences"][0]["confidence"]
    plagiarism_confidence = data[0]["confidences"][1]["confidence"]

    p, o = grading(original_confidence, plagiarism_confidence)

    # Store the variables in the session
    session["o"] = round(o)
    session["p"] = round(p)

    # Save the data to the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO projects (student_name, project_title, plagiarism_percentage, originality_percentage)
        VALUES (?, ?, ?, ?)
        """,
        (student_name, project_title, p, o)
    )
    db.commit()

    print('before redirect')
    # Render the result page HTML template with the plagiarism check results
    return redirect(url_for("result"))

@app.route("/result")
def result():
    # Retrieve the variables from the session
    o = session.get("o")
    p = session.get("p")

    # Render the result page HTML template with the plagiarism check results
    return render_template("result.html", o=o, p=p)

def save_file(file):
    # Generate a unique filename for the uploaded file
    filename = str(uuid.uuid4()) + ".pdf"
    upload_dir = os.path.join(app.root_path, "uploads")  # Path to the 'uploads' directory
    os.makedirs(upload_dir, exist_ok=True)  # Create the 'uploads' directory if it doesn't exist
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    return file_path

def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

app.teardown_appcontext(close_db)

if __name__ == "__main__":
    app.run(debug=True)
