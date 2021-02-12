# set environment variables:
export MYSQL_USER="vog"
export MYSQL_PASSWORD="password"
export MYSQL_HOST="localhost:3306"
export MYSQL_DATABASE="vogdb"
export VOG_DATA="data/"
export NCBI_DATA=$HOME/.etetoolkit/

# run test script
pytest tests/test_vogdb_main.py
