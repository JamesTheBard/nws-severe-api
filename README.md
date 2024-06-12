# Quickstart

## Prerequisites

- Docker and Docker Compose installed
- `webfsd` installed (if serving images with `webfs`)
- Poetry installed (for dependency management)

## Instructions

1. Start the database.

   ```
   cd docker
   sudo docker compose up -d
   cd ..
   ```

2. Start the webserver.  For `webfs`, just run the `run_server_webfs.sh` script.

   ```
   sh run_server_webfs.sh
   ```

   If you want to use Python to serve images:

   ```
   sh run_server_python.sh
   ```

3. Install all dependencies.

   ```
   poetry install
   ```

3. Start the updater service.

   ```
   poetry run python update.py
   ```