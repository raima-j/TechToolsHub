from flask import Blueprint, render_template, request, redirect, flash, url_for
import os
import camelot
import pandas as pd
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# Define the Blueprint
tool2_bp = Blueprint('tool2', __name__, static_folder='static', template_folder='templates')

# Define base directories for assets
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)

# Paths to Tesseract and Poppler binaries (if applicable for Tool 2)
tesseract_path = os.path.join(project_dir, 'Assets', 'Tesseract-OCR', 'tesseract.exe')
poppler_path = os.path.join(project_dir, 'Assets', 'Release-24.02.0-0', 'poppler-24.02.0', 'Library', 'bin')

@tool2_bp.route('/', methods=['GET', 'POST'])
def tool2_index():
    if request.method == 'POST':
        # Retrieve form data
        start_page = request.form.get('start_page', '').strip()
        end_page = request.form.get('end_page', '').strip()
        specify_pages = request.form.get('specify_pages', '').strip()
        pdf_path = request.form.get('pdf_path', '').strip()
        file_name = request.form.get('file_name', '').strip()
        save_path = request.form.get('save_path', '').strip()

        # Check if required fields are filled
        if not pdf_path or not file_name or not save_path or (not start_page and not end_page and not specify_pages):
            flash("Please enter all required details", 'error')
            return redirect(url_for('tool2.tool2_index'))

        try:
            # Convert entries to integers where applicable
            start_page = int(start_page) if start_page else 0
            end_page = int(end_page) if end_page else 0

            # Extract tables based on the page range
            if start_page and end_page:
                tables = camelot.read_pdf(pdf_path, flavor='stream', pages=f'{start_page}-{end_page}')
                process_tables(tables, save_path, file_name, start_page=start_page)

            # Extract tables from specific pages
            elif specify_pages:
                tables = camelot.read_pdf(pdf_path, flavor='stream', pages=specify_pages)
                process_tables(tables, save_path, file_name)

            flash('Tables extracted successfully.', 'success')

        except Exception as e:
            flash(f"Error: {str(e)}", 'error')

        return redirect(url_for('tool2.tool2_index'))

    return render_template('tool2_index.html')

def process_tables(tables, save_path, file_name, start_page=0):
    """Processes and saves the extracted tables to an Excel file."""
    if tables:
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        with pd.ExcelWriter(os.path.join(save_path, f'{file_name}.xlsx'), engine='xlsxwriter',
                            engine_kwargs={'options': {'strings_to_numbers': True}}) as writer:
            for i, table in enumerate(tables):
                table_df = table.df
                table_df = table_df.apply(pd.to_numeric, errors='ignore')
                page_number = start_page + i if start_page else i + 1
                tab_name = f"Page_{page_number}" if start_page else f"Table_{page_number}"
                table_df.to_excel(writer, index=False, sheet_name=tab_name)

