import re
import spacy
from flask import Flask, request, render_template_string
from PyPDF2 import PdfReader

# Load the spaCy English NLP model
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)

# Regular expressions for extracting structured information
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{10,}\b'
PHONE_REGEX = r'\b(\+?\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
TECH_REGEX = r'\b(Python|Java|C\+\+|JavaScript|SQL|HTML|CSS|React|Django|Flask)\b'

# Function to extract text from PDF
def extract_pdf_text(pdf):
    reader = PdfReader(pdf)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""  # Handling cases where extract_text returns None
    return text

# Function to parse the resume using NLP
def parse_resume_nlp(text):
    doc = nlp(text)

    # Extract person's name
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":  # spaCy can identify people entities
            name = ent.text
            break

    # Extract organizations (used for education and work experience)
    organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

    # Extract dates for education/work experience (for timeframes)
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    # Use regex to find emails, phones, and technologies
    email = re.findall(EMAIL_REGEX, text)
    phone = re.findall(PHONE_REGEX, text)
    technologies = re.findall(TECH_REGEX, text)

    return {
        "name": name if name else "Name not found",
        "email": email[0] if email else "Email not found",
        "phone": phone[0] if phone else "Phone number not found",
        "education": organizations,  # Assuming orgs can be used for education/work
        "work_experience": organizations,
        "technologies": ", ".join(set(technologies)) if technologies else "Technologies not found",
        "dates": dates
    }

# Simple HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Resume Parser</title>
</head>
<body>
    <h1>Upload Resume</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume" required>
        <input type="submit" value="Upload">
    </form>

    {% if result %}
        <h2>Parsed Data:</h2>
        <p><strong>Name:</strong> {{ result.name }}</p>
        <p><strong>Email:</strong> {{ result.email }}</p>
        <p><strong>Phone:</strong> {{ result.phone }}</p>
        <p><strong>Education/Work Experience:</strong> {{ result.education }}</p>
        <p><strong>Technologies:</strong> {{ result.technologies }}</p>
        <p><strong>Dates:</strong> {{ result.dates }}</p>
    {% endif %}
</body>
</html>
'''

# Flask route for handling the upload and parsing
@app.route('/', methods=['GET', 'POST'])
def upload_resume():
    result = None
    if request.method == 'POST':
        file = request.files['resume']
        if file and file.filename.endswith('.pdf'):
            pdf_text = extract_pdf_text(file)
            result = parse_resume_nlp(pdf_text)
        else:
            result = {"error": "Invalid file format. Please upload a PDF."}

    return render_template_string(HTML_TEMPLATE, result=result)

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
