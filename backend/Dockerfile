# If python version change is needed, do it here as well!
FROM python:3.9.23

WORKDIR /app 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

# Flask port
EXPOSE 5000 

CMD ["flask", "run"]
