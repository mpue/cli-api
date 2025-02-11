# CLI Runner - REST API Wrapper for Command-Line Programs

## Overview
CLI Runner is a FastAPI-based REST service designed to encapsulate command-line programs, allowing them to be executed through a RESTful interface. The application supports:

- **File Uploads & Downloads**: Users can upload files that will be passed as arguments to CLI programs.
- **Execution of CLI Commands**: Commands are executed within a secure Docker container.
- **FastAPI Integration**: A lightweight, high-performance API for command execution.

## Features
- 🚀 Execute arbitrary command-line programs via REST API.
- 📁 Upload and use files as input parameters for commands.
- 📤 Download generated files from the execution process.
- 🐳 Runs inside a Docker container for isolation and security.
- 🔥 Built with FastAPI for speed and efficiency.

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/your-username/cli-runner.git
cd cli-runner
```

### 2. Install Dependencies (Using Poetry)
```sh
poetry install
```

### 3. Run Locally (Without Docker)
```sh
poetry run uvicorn cli_runner.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Build & Run in Docker
#### Build the Docker Image
```sh
docker build -t cli-runner-api .
```
#### Run the Docker Container
```sh
docker run --rm -p 8000:8000 -v $(pwd)/uploads:/app/uploads cli-runner-api
```

## API Usage

### Upload a File
```sh
curl -X POST "http://localhost:8000/upload/" -F "file=@testfile.txt"
```
#### Response:
```json
{
    "filename": "testfile.txt",
    "filepath": "/app/uploads/testfile.txt"
}
```

### Execute a Command with a File
```sh
curl -X POST "http://localhost:8000/run/" -F "command=cat" -F "filename=testfile.txt"
```
#### Response:
```json
{
    "command": "cat /app/uploads/testfile.txt",
    "returncode": 0,
    "stdout": "File content...",
    "stderr": ""
}
```

### Download a File
```sh
curl -X GET "http://localhost:8000/download/testfile.txt" -o downloaded_file.txt
```

## Configuration
### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_DIR` | Directory for uploaded files | `/app/uploads` |
| `PORT` | Port on which FastAPI runs | `8000` |

## Future Enhancements
- ✅ Add authentication for API security.
- ✅ Implement a job queue for long-running commands.
- ✅ Improve logging and monitoring with Prometheus/Grafana.

## License
This project is licensed under the MIT License.

## Contact
For questions or contributions, open an issue on GitHub.

