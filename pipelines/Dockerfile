FROM python:3.9.23 

WORKDIR /app 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

CMD ["python", "test.py"]