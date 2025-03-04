# Use an official Python runtime as a parent image
FROM python:3.14-rc-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /
COPY . /

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "main.py"]