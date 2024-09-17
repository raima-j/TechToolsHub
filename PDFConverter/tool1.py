from flask import Flask, render_template, request, redirect, flash, url_for
import os
from pdf2image import convert_from_path
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

# Configure maximum image pixels for PIL to avoid image size issues
Image.MAX_IMAGE_PIXELS = 933120000


from flask import Blueprint, render_template

tool1_bp = Blueprint('tool1', __name__, static_folder='static', template_folder='templates')

@tool1_bp.route('/')
def index():
    return render_template('tool1_index.html')  # Make sure this template is in Tool1/templates

# Define base directories for assets
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)

# Paths to Tesseract and Poppler binaries
tesseract_path = os.path.join(project_dir, 'Assets', 'Tesseract-OCR', 'tesseract.exe')
poppler_path = os.path.join(project_dir, 'Assets', 'Release-24.02.0-0', 'poppler-24.02.0', 'Library', 'bin')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flashing messages


@tool1_bp.route('/convert', methods=['POST'])
def convert_to_text():
    """Handle the PDF to text conversion."""
    input_folder = request.form['input_folder']
    output_folder = request.form['output_folder']
    
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    os.environ['TESSDATA_PREFIX'] = os.path.join(project_dir, 'Assets', 'Tesseract-OCR')

    if input_folder and output_folder:
        pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
        total = len(pdf_files)
        text_files = [f for f in os.listdir(output_folder) if f.endswith('.txt')]

        remaining_files = total

        def process_pdf(pdf_file):
            """Processes a single PDF file, extracts text, and saves it to a text file."""
            nonlocal remaining_files
            name = os.path.splitext(pdf_file)[0]
            try:
                # Skip processing if the text file already exists
                if f"{name}.txt" in text_files:
                    remaining_files -= 1
                    return
                images = convert_from_path(os.path.join(input_folder, pdf_file), poppler_path=poppler_path)
                text = ""
                for page in images:
                    text += pytesseract.image_to_string(page)
                with open(os.path.join(output_folder, f"{name}.txt"), 'w', encoding='utf-8') as txt_file:
                    txt_file.write(text)

                remaining_files -= 1
            except Exception as e:
                flash(f"Error processing {pdf_file}: {e}", 'danger')

        # Use ThreadPoolExecutor to process PDF files concurrently
        with ThreadPoolExecutor() as executor:
            executor.map(process_pdf, pdf_files)

        flash(f"Conversion complete! Processed {total} PDF files.", 'success')
    else:
        flash("Please provide valid input and output folder paths.", 'warning')

    return redirect(url_for('tool1.index'))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
