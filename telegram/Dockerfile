# Use a lightweight Python base image
FROM python:3.14-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application script
COPY lgtm_command.py .

# Command to run the bot when the container starts
# The script uses run_polling(), which runs indefinitely
CMD ["python", "lgtm_command.py"]