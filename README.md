# saaga-api

The SAAGA project aims to create an automated pipeline for characterizing chemical mixtures of gas phase using experimental rotational spectroscopy with the help of machine learning and other computational tools. An important part is to have a database of rotational spectrum of a comprehensive list of known species, as well as a RESTful API to allow convenient and efficient access and queries to the database.

The database is already set up and hosted on Amazon RDS. The RESTful API allows CRUD operations of the database, in which admins can perform the full CRUD operations while other users can read and query the database.
The API is under development and the database is yet to be filled with data. The API is written using Python and Django with Docker. The setup of the API is done, and database model development is in progress right now.

# Commands

## Run the app and database container using docker compose in background

### Production

`docker-compose -p prod -f docker-compose-deploy.yml up -d`

### Development

`docker-compose -p dev -f docker-compose.yml up -d`

_Note: the `-p` flag is used to specify the project name, which is used as the prefix of the container name. This is useful when running multiple docker-compose files at the same time._

### Login as a root user in the app container

`docker exec -u 0 -it dev_app_1 /bin/bash`
- `docker exec`: This is the Docker command to run a command in a running container.
- `-u 0`: This option specifies that the command should be run as the root user.
- `-it`: These options make the command interactive (-i) and allocate a pseudo-TTY (-t), which makes it feel like you're directly typing in the container's terminal.
- `dev_app_1`: This should be replaced with the name or ID of your container.
- `/bin/bash`: This is the command to run in the container. It starts a Bash shell.


## Create a superuser

`docker-compose -p prod -f docker-compose-deploy.yml run --rm app sh -c ‘python manage.py createsuperuser`

Create a superuser with email and password
Now navigate to <http://localhost:8000/api/user/token> and login with the superuser credentials to get the token

Authenticate with the token in the header of the request
`Token <token>`


## Logging in as a root user in docker teminal

`docker exec -u 0 -it container_name /bin/bash`

 - `docker exec`: This is the Docker command to run a command in a running container.
 - `-u 0`: This option specifies that the command should be run as the root user.
 - `-it`: These options make the command interactive (-i) and allocate a pseudo-TTY (-t), which makes it feel like you're directly typing in the container's terminal.
container_name`: This should be replaced with the name or ID of your container.
 - `/bin/bash`: This is the command to run in the container. It starts a Bash shell.

After running this command, you'll be logged into the container as the root user and can run any commands you need.

This is usefull to run commands like `python manage.py makemigrations`, `python manage.py migrate` or `python manage.py createsuperuser` in the container.

## Connect to the database

`docker-compose -p prod -f docker-compose-deploy.yml run db psql postgresql://rootuser:saagadb@db:5432/dbname`

if needed replace (as defined in the docker-compose file) or .env file:
- `rootuser` with the username
- `saagadb` with the password
- `5432` with the port
- `dbname` with the database name


## Reset the database

```bash
\dt # To check the table list in the database
DROP SCHEMA public CASCADE; # To drop the schema
CREATE SCHEMA public; # To create the schema
```

restart the docker container
