FROM python:3.10-slim

LABEL author="Student Team"
LABEL description="NLP Assignment - Intelligent Course Assistant"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /nlp

# Copy dependencies first for layer caching
COPY requirements.txt /nlp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /nlp/requirements.txt

# Copy all project files
COPY . /nlp/

# Create input and output directories if not exist
RUN mkdir -p /nlp/input /nlp/output

# Default command runs the main pipeline
CMD ["python3", "-m", "src.main"]
