from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import cohere
from utils.pdf_reader import extract_text_from_pdf
from utils.section_splitter import split_sections
from utils.format_text import format_section_text
from xhtml2pdf import pisa
import io
from gtts import gTTS
import uuid
from bs4 import BeautifulSoup
import json

from models import db, User, Report  # 💡 import models

# Flask app setup
app = Flask(__name__)
app.secret_key = "sruti123@"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projpal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Login manager setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load environment
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)

# Helper functions
def clean_html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=' ')

def rephrase_text(text, tone, audience, mode="normal"):
    note = ""
    if len(text) > 2000:
        text = text[:2000]
        note = "⚠️ Note: Section was too long and has been truncated.\n\n"

    mode_instruction = {
        "normal": "",
        "eli5": "Explain it like I'm 5 years old.",
        "professor": "Explain it in a very academic and detailed manner.",
        "meme": "Use memes or humor in the explanation."
    }

    prompt = f"""{mode_instruction.get(mode, '')}\n\nRephrase the following project section as a {audience}, using a {tone} tone:\n\n{text}"""

    try:
        response = co.generate(
            model='command-light',
            prompt=prompt,
            max_tokens=300,
            temperature=0.7
        )
        return note + response.generations[0].text.strip()
    except Exception as e:
        return f"⚠️ Error from Cohere API: {str(e)}"

def generate_mermaid_diagram(sections):
    diagram = "graph TD\n"
    for i, (title, content) in enumerate(sections.items()):
        node = f"A{i}[{title}]"
        diagram += f"    {node}\n"

        # Split content and add more links based on section relationships
        # (this is just a simple example, you can customize this)
        if i > 0:
            diagram += f"    A{i-1} --> {node}\n"

        if "Conclusion" in title:
            diagram += f"    A{i} --> A{len(sections)}[End]\n"
    return diagram


# Routes
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    extracted_text = ''
    sections = {}
    rephrased_sections = {}
    cleaned_sections = {}

    if request.method == 'POST':
        pdf = request.files.get('pdf')
        tone = request.form.get('tone')
        role = request.form.get('role')
        mode = request.form.get('mode')  # capture the mode

        if pdf:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf.filename)
            pdf.save(filepath)

            extracted_text = extract_text_from_pdf(filepath)
            sections = split_sections(extracted_text)

            for title, content in sections.items():
                rephrased = rephrase_text(content, tone, role, mode)
                formatted = format_section_text(rephrased)
                rephrased_sections[title] = formatted
                cleaned_sections[title] = clean_html_to_text(formatted)

            report = Report(user_id=current_user.id, sections=json.dumps(cleaned_sections))
            db.session.add(report)
            db.session.commit()
    
    diagram=generate_mermaid_diagram(sections)

    return render_template('index.html', text=extracted_text, sections=cleaned_sections, diagram=diagram)

@app.route('/download', methods=['POST'])
@login_required
def download_pdf():
    sections = json.loads(request.form.get('sections_data'))
    html = render_template('download.html', sections=sections)
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name="Rephrased_Project.pdf", as_attachment=True)

@app.route('/audio', methods=['POST'])
def audio():
    text = request.form.get('text')
    if not text:
        return {"error": "No text provided"}
    audio_path = generate_audio(text)
    filename = os.path.basename(audio_path)
    return {"audio_url": f"/static/audio/{filename}", "transcript": text}

def generate_audio(text, lang='en'):
    filename = f"{uuid.uuid4()}.mp3"
    path = os.path.join("static", "audio", filename)
    gTTS(text=text, lang=lang).save(path)
    return path

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']

        if User.query.filter_by(email=email).first():
            flash("⚠️ Email already registered. Please login or use another email.", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(contact=contact).first():
            flash("⚠️ Contact number already registered. Please use a different one.", "danger")
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password=password,
            age=age,
            gender=gender,
            contact=contact
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered! Please login.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('welcome'))

@app.route('/history')
@login_required
def history():
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.timestamp.desc()).all()
    return render_template('history.html', reports=reports)

@app.route('/')
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('welcome.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        user = current_user
        user.username = request.form['username']
        user.email = request.form['email']
        user.age = request.form['age']
        user.gender = request.form['gender']
        user.contact = request.form['contact']
        db.session.commit()
        flash("Profile updated successfully!")
    return render_template('profile.html', user=current_user)

@app.route('/ai-facts')
@login_required
def ai_facts():
    return render_template('ai_facts.html')


# @app.route("/login")
# def login():
#     return render_template("login.html")

# @app.route("/register")
# def register():
#     return render_template("register.html")

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port,debug=True)