# Define the base image
FROM python:3.10.2

# Set the working directory
RUN mkdir -p /app_user

# Copy the application files
COPY . /app_user

# Install dependencies
RUN python3 -m pip install -r /app_user/requirements.txt

# Expose the port
EXPOSE 5000

# Define the startup command
CMD [ "python", "/app_user/app.py" ]
