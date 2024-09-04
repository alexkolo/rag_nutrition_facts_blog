# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY ./middleware/ /app

# Install the necessary packages
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=middleware.py

# Run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
