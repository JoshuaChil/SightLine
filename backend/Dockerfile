# If python version change is needed, do it here as well!
FROM python:3.9.23

WORKDIR /app 

#COPY requirements.txt .

#RUN pip install --no-cache-dir -r requirements.txt 
RUN pip install Flask

COPY . .

# Flask port
EXPOSE 5000 

# -w {num} is for worker threads, increase to handle more capacity (most likely won't need to)
CMD ["flask", "run"]