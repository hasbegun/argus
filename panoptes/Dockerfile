# Use a lightweight Python base image
FROM python:3.13-slim

# Add pkgs for opencv2
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y libgl1 libgl1-mesa-glx libglib2.0-0

# Set the working directory in the container
WORKDIR /app

# Copy in your requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm -f requirements.txt

# Copy the rest of your app code
COPY ./src .
RUN rm -f .env

# Expose port 3000 (the port where FastAPI will run)
EXPOSE 3000

# Default command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
