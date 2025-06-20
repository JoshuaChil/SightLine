# If python version change is needed, do it here as well!
FROM python:3.9.23

WORKDIR /app 

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

# Install production server
RUN pip install gunicorn

COPY . .

# Flask port
EXPOSE 8080

# -w {num} is for worker threads, increase to handle more capacity (most likely won't need to)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
