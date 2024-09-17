# Use a specific Python image for consistency
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app/TechToolsHub

# Copy the entire project (including assets folder) into the container
COPY . /app/TechToolsHub/

# Install the Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Tesseract and Poppler paths inside the container
ENV TESSDATA_PREFIX="/app/TechToolsHub/Assets/Tesseract-OCR/"
ENV POPPLER_PATH="/app/TechToolsHub/Assets/Release-24.02.0-0/poppler-24.02.0/Library/bin/"

# Expose the port that Flask will run on (if you're running a Flask app)
EXPOSE 5000

# Command to run the main Python script (Flask or another type of app)
CMD [ "python", "./app.py" ]
