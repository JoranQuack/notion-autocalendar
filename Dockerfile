# Use an official Python runtime as a parent image
FROM python:3.13.1-alpine

# switch working directory
WORKDIR /app

# copy every content from the local file to the image
COPY . /app

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "main.py"]