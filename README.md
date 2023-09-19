# About this project
The problem: When moodle designed their database system most popular database systems did not support foreign keys. 
Therefore, they decided to implement them software side in moodle.
As of moodle 4.2 this is still the case.
As a result it is not possible to automatically generate useful database diagrams for moodle databases as they require foreign keys to show relations between tables.

The solution: This repository contains a script that creates rudimentary SQL CREATE TABLE statements for all tables in the moodle database. 
It implements just enough to create database diagrams as this is the only target of this script.
It is very likely that the created database will not work with moodle.

## compatible moodle versions
It is known that moodle 3.9, 3.11, 4.0 and 4.2 are working.

## How to use
The following assumes you are using WSL. It should work like that on linux as well.

You need a database running on your machine with the following configuration. 

db-system: mariadb \
host: localhost \
port: 3312 \
user: root \
password: a \

It is hardcoded in the script, but you should be able to change that easily.
You can use the following docker-compose file to start a database with the correct configuration:
```yaml
version: '3'
services:
  db_moodle:
    image: docker.io/bitnami/mariadb:10.6
    ports:
      - 3312:3306
    environment:
      MARIADB_USER: blub
      MARIADB_PASSWORD: blub
      MARIADB_ROOT_PASSWORD: a
      MARIADB_DATABASE: blub
      MARIADB_CHARACTER_SET: utf8mb4
      MARIADB_COLLATE: utf8mb4_unicode_ci
    volumes:
      - db_moodle_data:/bitnami/mariadb
    restart: unless-stopped
volumes:
    db_moodle_data:
```

1. Create a file `list_of_xmldb_files.txt` with the paths to all `install.xml` files of your moodle installation.
You can do this under linux with the following command:
```bash
find /path/to/moodle -name install.xml > list_of_xmldb_files.txt
```
2. Run the script with `python3 convert_xmldb_to_create_table_statements.py > create_tables.sql` to create a file with all SQL CREATE TABLE statements.
3. If the database `diagram` already exists (eg. from a previous run), drop it. `echo "DROP DATABASE diagram;" | mysql -h localhost -P 3312 -u root -pa`
4. Create the database and create the tables as described in the `create_tables.sql` file: `echo "CREATE DATABASE IF NOT EXISTS diagram;" | mysql -h localhost -P 3312 -u root -pa && cat create_tables.sql | mysql -h localhost -P 3312 -u root -pa -D diagram`
5. Now you can use any tool that can connect to a mariadb and create database diagrams from it (eg jetbrains IDEs or MySQL Workbench).

Attention: Moodle has a lot of tables. You will have to create a selection of tables you want to show in the diagram.