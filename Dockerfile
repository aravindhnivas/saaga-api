# Docker image, alpine is a lightweight version of linux which is ideal for running Docker containers because it's extremely lightweight and efficient.
FROM python:3.9-alpine

# Maintainer of the software for now.
LABEL maintainer="jsycheung"

# Tells Python not to buffer the output, prevent any delay in message from python to the screen so that we can see the logs immediately as they are running.
ENV PYTHONUNBUFFERED 1

# Copy files and folder into docker image.
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
# Default directory that our commands run from.
WORKDIR /app
# Expose port 8000 from the container to our machine when we run the container and connect to django server.
EXPOSE 8000

ARG DEV=false

# Create new virtual environment where we install dependencies to avoid conflicting dependencies between the image and the project.
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache git && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev && \
    # Install requirements inside docker image.
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    # Remove the temporary directory after we install dependencies to keep docker image as lightweight as possible.
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    # Add new user inside the image, it's best practice not to use the root user which has full access to do everything on the server.
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

# Run Python command automatically from virtual environment.
ENV PATH="/py/bin:$PATH"

# Specify the user that we are switching to.
USER django-user