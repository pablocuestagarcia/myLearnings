# PostgreSQL Meta-Commands



| Command       | Description                                                                                        | Example                                           |
|---------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `\c`          | Connect to a new database (`\c [database_name] [user_name]`).                                      | `\c my_database my_user`                          |
| `\dt`         | List all tables in the current database schema.                                                    | `\dt`                                             |
| `\d`          | Describe a table, view, sequence, or index (`\d [object_name]`).                                   | `\d my_table`                                     |
| `\l`          | List all databases in the PostgreSQL server.                                                       | `\l`                                              |
| `\du`         | List all roles (users and groups) in the PostgreSQL server.                                        | `\du`                                             |
| `\dn`         | List all schemas in the current database.                                                          | `\dn`                                             |
| `\df`         | List all functions in the current database.                                                        | `\df`                                             |
| `\dv`         | List all views in the current database.                                                            | `\dv`                                             |
| `\di`         | List all indexes in the current database.                                                          | `\di`                                             |
| `\timing`     | Toggle display of how long each SQL statement takes to execute.                                    | `\timing`                                         |
| `\q`          | Quit psql.                                                                                         | `\q`                                              |
| `\e`          | Open the current query buffer in the default text editor.                                          | `\e`                                              |
| `\s`          | Display command history.                                                                           | `\s`                                              |
| `\i`          | Execute commands from a file (`\i [file_name]`).                                                   | `\i my_script.sql`                                |
| `\h`          | Help on SQL commands (`\h [command]`).                                                             | `\h SELECT`                                       |
| `\?`          | Help on psql commands.                                                                             | `\?`                                              |
| `\x`          | Toggle expanded table output (`\x` or `\x on`/`\x off`).                                           | `\x`                                              |
| `\o`          | Send query results to a file or a program (`\o [file_name]` or `\o [program]`).                    | `\o output.txt`                                   |
| `\p`          | Print the current query buffer.                                                                    | `\p`                                              |
| `\g`          | Execute the query in the current buffer.                                                           | `\g`                                              |
| `\copy`       | Perform a SQL COPY with data stream to or from a file or program (`\copy [table] TO/FROM [file]`). | `\copy my_table TO 'output.csv' CSV HEADER;`      |
| `SELECT current_user;` | Show the current user.                                                                   | `SELECT current_user;`                            |
| `\conninfo`   | Show current connection information.                                                              | `\conninfo`                                       |
| `SELECT COUNT(*) FROM pg_catalog.pg_user;` | Count the total number of users.                                    | `SELECT COUNT(*) FROM pg_catalog.pg_user;`        |

### Additional Queries for Administration

| Query                                                                                  | Description                                                                                          | Example                                     |
|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `CREATE USER username WITH PASSWORD 'password';`                                       | Create a new user.                                                                                   | `CREATE USER new_user WITH PASSWORD 'pass';`|
| `ALTER USER username WITH PASSWORD 'new_password';`                                    | Change the password of an existing user.                                                             | `ALTER USER my_user WITH PASSWORD 'new_pass';`|
| `DROP USER username;`                                                                  | Delete an existing user.                                                                             | `DROP USER unwanted_user;`                  |
| `GRANT ALL PRIVILEGES ON DATABASE dbname TO username;`                                 | Grant all privileges on a database to a user.                                                        | `GRANT ALL PRIVILEGES ON DATABASE my_db TO my_user;`|
| `REVOKE ALL PRIVILEGES ON DATABASE dbname FROM username;`                              | Revoke all privileges on a database from a user.                                                     | `REVOKE ALL PRIVILEGES ON DATABASE my_db FROM my_user;`|
| `CREATE DATABASE dbname;`                                                              | Create a new database.                                                                               | `CREATE DATABASE new_db;`                   |
| `DROP DATABASE dbname;`                                                                | Delete an existing database.                                                                         | `DROP DATABASE unwanted_db;`                |
| `ALTER DATABASE dbname RENAME TO new_dbname;`                                          | Rename a database.                                                                                   | `ALTER DATABASE old_db RENAME TO new_db;`   |
| `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO username;`     | Grant specific privileges on all tables in a schema to a user.                                       | `GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO my_user;`|
| `REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM username;`  | Revoke specific privileges on all tables in a schema from a user.                                    | `REVOKE SELECT, INSERT ON ALL TABLES IN SCHEMA public FROM my_user;`|

This table includes commands with examples, and additional useful queries for database administration in PostgreSQL.