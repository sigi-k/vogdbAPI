from sqlalchemy import create_engine
import os



"""
Here we create our VOGDB and create all the tables that we are going to use
Note: you may need to change the path of the data folder and your MYSQL credentials
"""

def connect_to_database():
    data_path = "../data_testing/"

    # MySQL database connection
    username = os.environ.get("MYSQL_USER", "vog")
    password = os.environ.get("MYSQL_PASSWORD", "password")
    server = os.environ.get("MYSQL_HOST", "localhost:4000")
    database = os.environ.get("MYSQL_DATABASE", "vogdb_test")
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://{0}:{1}@{2}/{3}".format(username, password, server, database)


    # Create an engine object.
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
    engine.connect()
    return engine

