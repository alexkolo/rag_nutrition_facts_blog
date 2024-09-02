# Using official Python runtime as a parent image
FROM python:3.12-slim

# Upgrade pip, wheel, and setuptools to the latest version without using cache
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Install PyTorch packages from a specific index URL without cache
RUN pip install --no-cache-dir torch==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Set the working directory in the container
WORKDIR /app

# Copy the setup files and install the Python package
COPY setup.py setup.cfg /app/
RUN pip install --no-cache-dir  .

# Copy the rest of the application code into the container
COPY . /app

# Expose the port that Streamlit will run on
EXPOSE 8501

# Test a container to check that it is still working
# - it needs to listen to Streamlit’s (default) port 8501:
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1


# Run
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
