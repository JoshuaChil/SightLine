# Backend Server Information

This is the backend server that runs the application and pipelines, it is meant to run all in a docker container, which documentation for is provided below.

### How to run

Build container: `docker build -t visassistglasses:latest .`

Run container: `docker run -n visassistglasses -p 5000:5000 -d visassistglasses:latest`

### Development

Initialize virtual enviornment: `python -m venv .venv`

Activate environment: `.venv/Scripts/Activate.{ps1|bat}` or `source .venv/bin/activate`

Install requirements: `pip install -r requirements.txt`

Run development server: `flask run`