#!/bin/bash
# MySQL runs all .sql files in /docker-entrypoint-initdb.d/ alphabetically on first start
# This script runs them explicitly in order

set -e

mysql -u root -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init_user_db.sql
mysql -u root -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init_chef_db.sql
mysql -u root -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init_order_db.sql
mysql -u root -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init_delivery_db.sql
mysql -u root -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init_logging_db.sql

echo "All databases created."