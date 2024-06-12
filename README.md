# Quickstart

## Prerequisites

- Docker and Docker Compose installed
- `webfsd` installed (if serving images with `webfs`)
- Poetry installed (for dependency management)

## Instructions

1. Download all of the requisite data.

   ```
   sh populate_data.sh
   ```

2. Start the database.

   ```
   cd docker
   sudo docker compose up -d
   cd ..
   ```

3. Start the webserver.  For `webfs`, just run the `run_server_webfs.sh` script.

   ```
   sh run_server_webfs.sh
   ```

   If you want to use Python to serve images:

   ```
   sh run_server_python.sh
   ```

4. Install all dependencies.

   ```
   poetry install
   ```

5. Start the updater service.

   ```
   poetry run python update.py
   ```