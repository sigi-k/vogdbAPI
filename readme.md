# VOGDB-API

## Introduction
The Virus Orthologous Groups Database Application Programming Interface (VOGDB-API) provides access to the stored data in a more elaborate way. Orthologous groups can be filtered based on numerous criteria, enabling the user to make more specific searches. Additionally, the Hidden Markov Matrices (HMMs) and Multiple Sequence Alignments (MSAs) for VOGs, as well as Aminoacid and Nucleotide sequences for proteins can be retrieved.

## Running in Docker

### Installing Docker

```bash
sudo apt-get install docker.io docker-compose
sudo addgroup <username> docker
```
Maybe for preparation you have to do:
```bash
sudo systemctl disable --now mysql.service
```
to free the port for the docker container.

### Services

Currently two services are defined in `docker-compose.yaml`:

* db

  This is the Mysql database server.

  You start the db service with
  ```bash
  docker-compose up -d db
  ```
  Because `app` has a dependency on `db`
  it will also be started when you start the `app` container.

  Currently port 3306 is exposed from the db service to facilitate local development. This is **not** required/recommended in production.

* app

  This is the application (i.e. the FastAPI server). By default, it is hosted in `uvicorn`, but
  this can be changed in `docker-compose.yaml` to `hypercorn`.

  You start the app service with
  ```bash
  docker-compose up -d app
  ```
  Because of the dependency the db service will also be started.
  The app container also contains two data loading jobs `load-vog` and `load-taxa`. Because these are not long-running services, they have to be started by
  ```bash
  docker-compose run --rm app <job>
  ```
  job is either `load-vog` or `load-taxa`.
  `load-vog` takes an optional version parameter, if it is not provided, the latest version is downloaded. A specific version can be loaded with
  ```bash
  docker-compose run --rm app load-vog 202
  ```
### Volumes

Data is stored on persistent volumes, therefore
```bash
docker-compose down
```
will leave the database and other data intact, whereas 
```bash
docker-compose down -v
```
will remove the volumes and you will have to start from scratch, i.e. reload the databases. Note that loading the database will take a few minutes. <br>


### Log Inspection
You can inspect the logs with
```bash
docker-compose logs [service...]
```
A running log is obtained by
```bash
docker-compose logs -f
```

All the commands above assume that you are running docker-compose from the directory where the docker-compose.yaml is stored. Otherwise (e.g. in crontab) you will have to specify the full path 
when you invoke docker-compose.
```bash
docker-compose -f /path/to/docker-compose.yaml run --rm app load-vog
```

### Building the images

If you change the definition of the app image (i.e. in the `Dockerfile`) or you want to include new/changed sources in the container, you will have to rebuild them by issueing
```bash
docker-compose build
```

### Removing images and containers
```bash
docker image ls
```
will list the built images. When you issue the build command, old images will be inactive, but they will remain stored on the disk.
You can free disk space with
```bash
docker image prune
```
which will remove unused ("dangling") images. <br>

You can remove individual images and containers with
```bash
docker image rm [image_id1] [image_id2]
docker container rm [container_id]
```


## Using the VOGDB-API with vDirect
VDirect is a user-friendly command line tool that creates URLs to make API requests for information retrieval via the VOGDB-API.
It can be found on PyPI and installed with:
```bash
pip install vDirect
```

## Authors
```bash
Monika Fink*, Nikola Vinko*, Sigi Koizar*

*University of Vienna
```