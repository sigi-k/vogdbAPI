#Deployment

## Docker containers
The docker-compose file will get the images from Dockerhub. The latest image of the API will be pulled.
Access to the MySQL port is removed in the deployment setting. 

## cronjob
A cronjob updates the DB on a regular basis.
##