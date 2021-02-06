import os
from vogdb import api
import uvicorn

# set the variables:
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_USER"] = "vog"
os.environ["MYSQL_PASSWORD"] = "password"
os.environ["MYSQL_DATABASE"] = "vogdb"


uvicorn.run(api, port=8000)
