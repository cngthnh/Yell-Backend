# Use Python37
FROM python:3.7

# Copy requirements.txt to the docker image and install packages
COPY requirements.txt /
RUN pip install -r requirements.txt

# Copy files to app folder
COPY . /app

# Expose port 80
EXPOSE 443
ENV PORT 443

# Set the WORKDIR to be the app folder
WORKDIR /app

# Use gunicorn as the entrypoint
CMD exec gunicorn --bind :$PORT yell_backend:app --workers 1 --threads 1 --timeout 60 --log-level 'debug'