#Deployment

## Docker containers
The docker-compose file will get the images from Dockerhub. The 1.0 image of the API will be pulled.
Access to the MySQL port is removed in the deployment setting. 
To start the services in detach-mode, simply type:
```bash
docker-compose up -d
```


## cron
Cronjobs are scheduled weekly to monitor the VOGDB fileshare site as well as the NCBI-Taxonomy site.
If there are modified files, the load-vog and load-taxa scripts are executed. Information and error
messages are logged in vog.log and taxa.log, respectively.
##