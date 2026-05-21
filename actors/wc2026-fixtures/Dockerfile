# Apify Python Actor base image
FROM apify/actor-python:3.11

# Copy requirements first (Docker layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy actor source
COPY . ./

# Run
CMD ["python", "main.py"]
