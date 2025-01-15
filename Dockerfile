# Use Python 3.9.6 slim image
FROM python:3.9.6-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container (including .env)
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=slack_email_qa_flask.py
ENV FLASK_ENV=production

# Expose port 8080 to access the Flask app
EXPOSE 8080

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
