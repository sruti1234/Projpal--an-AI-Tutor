import fitz  # PyMuPDF

def extract_text_from_pdf(filepath):
    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text
