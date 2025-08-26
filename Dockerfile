# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install any needed dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable for Flask app
ENV FLASK_APP=app.py # Replace with your main Flask app file

# Run the Flask app with Gunicorn (recommended for production)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app.py:app