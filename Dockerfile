# Use the official Python image as a base image
FROM python:3.10

# Install ODBC driver and dependencies (example for Debian/Ubuntu-based systems)
RUN apt-get update \
    && apt-get install -y gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev


# Set environment variables
ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script into the container at /usr/src/app
COPY entrypoint.sh .

# Set the entrypoint script as executable
RUN chmod +x entrypoint.sh

# Copy the project files into the container at /usr/src/app
COPY . .

# Expose port 8000 to allow communication to/from the web server
EXPOSE 8000

# Command to run the application using the entrypoint script
CMD ["./entrypoint.sh"]
