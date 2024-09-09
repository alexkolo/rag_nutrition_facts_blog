# build from root: `docker build -f dashboard/Dockerfile -t dashboard .`
# docker run -p 8080:8080 dashboard

# Using official Python runtime as a parent image
FROM python:3.12-slim

# Upgrade pip, wheel, and setuptools to the latest version without using cache
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Set the working directory in the container
WORKDIR /app

# Copy the setup files and install the Python packages
COPY ./dashboard/requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY ./dashboard /app

# Copy the config file
COPY ./rag_config.toml /app

# copy sectret folder
RUN mkdir -p /app/.streamlit
COPY ./.streamlit/secrets.toml /app/.streamlit

# Expose the port that Streamlit will run on
EXPOSE 8080

# Test a container to check that it is still working
# - it needs to listen to Streamlit’s port 8080:
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Set an environment variable to indicate the script is running inside a Docker container
ENV RUNNING_IN_DOCKER=1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
