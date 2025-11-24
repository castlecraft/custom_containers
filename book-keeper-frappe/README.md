# Book-Keeper Frappe

This repository contains the necessary configuration to set up a local development and testing environment for the [Book-Keeper](https://citadel.castlecraft.in/services/book-keeper/index) service. It uses Docker Compose to orchestrate the `book-keeper` application along with its dependencies: TigerBeetle, NATS, and KurrentDB.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker**: Get Docker
- **Docker Compose**: Install Docker Compose
- **Python 3**: The test script is written in Python.

## Local Development Setup

Follow these steps to get the environment up and running.

### 1. Start the Services

The `develop.yaml` file defines all the services required for the `book-keeper` application to run. Start them using Docker Compose:

```bash
docker compose -p book-keeper -f develop.yaml up -d
```

This command will:
- Use the project name `book-keeper` (`-p book-keeper`).
- Pull the required Docker images for `book-keeper`, `tigerbeetle`, `nats`, and `kurrentdb`.
- Create and start the containers in detached mode (`-d`).

The `book-keeper` API will be available at `http://localhost:9000`.

### 2. Run the API Test Suite

A Python test script (`test_bookkeeper.py`) is included to verify that the API is working correctly.

First, set up a Python virtual environment and install the required `httpx` library:

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install httpx
```

Now, run the test script:

```bash
python test_bookkeeper.py
```

If all tests pass, you will see a success message indicating that all scenarios completed successfully.

### 3. Shutting Down

To stop and remove the containers, network, and volumes created by Docker Compose, run:

```bash
docker compose -p book-keeper -f develop.yaml down
```
