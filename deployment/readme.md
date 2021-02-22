#Deployment

## Docker containers
The docker-compose file will get the images from Dockerhub. The 1.0 image of the API will be pulled.
Access to the MySQL port is removed in the deployment setting. 
To start the services in detach-mode, simply type:
```bash
docker-compose up -d
```


## cronjob
A cronjob updates the VOGDB as well as the NCBI-Taxonomy data once a week.
##