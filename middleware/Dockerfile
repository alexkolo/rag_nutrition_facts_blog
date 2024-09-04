# build: docker build -t middleware:latest ./middleware
# run: docker run --env-file docker.env -p 5000:5000 -d middleware:latest
# check container: docker run --env-file docker.env -it middleware:latest /bin/sh
# stop it: `docker stop <container id>` ( get Id with `docker ps` )
# check logs: docker logs <container id>

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
# "." from the directory of the dockerfile
COPY ./requirements.txt /app

# Install the necessary packages
RUN pip install --no-cache-dir -r requirements.txt

# copy source
COPY ./middleware.py /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
# ENV FLASK_APP=middleware.py

# Run the application
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "middleware:app"]
