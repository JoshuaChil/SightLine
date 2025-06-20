# If python version change is needed, do it here as well!
FROM python:3.13.5

WORKDIR /app 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

# Flask port
EXPOSE 5000 

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]