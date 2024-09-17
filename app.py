from flask import Flask, render_template, redirect, url_for

from PDFConverter.tool1 import tool1_bp
from TableExtractor.tool2 import tool2_bp
from AISummariser.tool4 import tool4_bp

app = Flask(__name__)
app.secret_key = "123qwerty890"


app.register_blueprint(tool1_bp, url_prefix='/tool1')
app.register_blueprint(tool2_bp, url_prefix='/tool2')
app.register_blueprint(tool4_bp, url_prefix='/tool4')

@app.route('/')
def dashboard():
    return render_template('index.html')  # Dashboard HTML template

if __name__ == "__main__":
    app.run(debug=True)