from flask import Blueprint, request, redirect, url_for, render_template, flash
import os
import pytesseract
from transformers import BartTokenizer, BartForConditionalGeneration
from pdf2image import convert_from_path
import csv
from natsort import natsorted
from concurrent.futures import ThreadPoolExecutor

tool4_bp = Blueprint('tool4', __name__, static_folder='static', template_folder='templates')

# Set up paths and directories
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)

tesseract_path = os.path.join(project_dir, 'Assets', 'Tesseract-OCR', 'tesseract.exe')
poppler_path = os.path.join(project_dir, 'Assets', 'Release-24.02.0-0', 'poppler-24.02.0', 'Library', 'bin')

model_name = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def summarize_text(text_chunk):
    inputs = tokenizer(text_chunk, return_tensors='pt', max_length=1024, truncation=True)
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']
    summary_ids = model.generate(input_ids, attention_mask=attention_mask, max_length=1024, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def process_files(file_paths, enable_ocr, output_dir, save_file):
    chunk_size = 1024
    context_chunk = 100

    def process_file(filepath, enable_ocr, output_dir, save_file):
        filename = os.path.basename(filepath)
        try:
            if filename.endswith('.pdf') and enable_ocr:
                if os.path.exists(poppler_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    os.environ['TESSDATA_PREFIX'] = os.path.join(project_dir, 'Assets', 'Tesseract-OCR')

                images = convert_from_path(filepath, poppler_path=poppler_path)
                text = ''
                for page in images:
                    page_text = pytesseract.image_to_string(page).lower()
                    text += page_text
            else:
                with open(filepath, 'r', encoding='utf-8') as file:
                    text = file.read()

            tokens = tokenizer(text, return_tensors='pt', truncation=False)['input_ids'][0]
            chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size - context_chunk)]

            summaries = [summarize_text(tokenizer.decode(chunk, skip_special_tokens=True)) for chunk in chunks]
            final_summary = ' '.join(summaries)

            output_file_path = os.path.join(output_dir, f"{save_file}.csv")
            with open(output_file_path, 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([f'=HYPERLINK("{filename}")', final_summary])

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    with ThreadPoolExecutor() as executor:
        executor.map(lambda fp: process_file(fp, enable_ocr, output_dir, save_file), file_paths)

@tool4_bp.route('/', methods=['GET', 'POST'])
def tool4_index():
    if request.method == 'POST':
        input_folder = request.form['input_folder']
        output_folder = request.form['output_folder']
        save_file = request.form['save_file']
        enable_ocr = 'enable_ocr' in request.form

        if not os.path.isdir(input_folder) or not os.path.isdir(output_folder):
            flash("Invalid directory paths provided.")
            return redirect(url_for('tool4.tool4_index'))

        file_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if allowed_file(f)]
        file_paths = natsorted(file_paths)

        if file_paths:
            process_files(file_paths, enable_ocr, output_folder, save_file)
            flash('Summaries have been generated.')
        else:
            flash('No valid files found in the input directory.')

        return redirect(url_for('tool4.tool4_index'))

    return render_template('tool4_index.html')
