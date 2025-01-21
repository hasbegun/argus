# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy in your requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm -f requirements.txt

# Copy the rest of your app code
COPY ./src .

# Expose port 3000 (the port where FastAPI will run)
EXPOSE 3000

# Default command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]

