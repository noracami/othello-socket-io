FROM python:3.11

# Set the working directory

WORKDIR /app

# Copy the current directory contents into the container at /app

COPY . /app

# Install any needed packages specified in requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "-w", "3", "--worker-class", "gevent", "--worker-connections", "1000", "-b", "0.0.0.0:8080", "app:app"]
