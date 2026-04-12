FROM python:3.10-slim

# Install system dependencies including FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scripts into the container
COPY organizer.py .
COPY database.py .

# Create the standard mount points for volumes
RUN mkdir /input_music
RUN mkdir /organized_library

# Command to naturally run the organizer using the volume mounts
ENTRYPOINT ["python", "organizer.py", "-i", "/input_music", "-o", "/organized_library"]
