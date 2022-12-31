# CEC REST API

REST API to control HDMI devices via the CEC protocol.

## Installation

Execute the following commands on a Debian or Ubuntu system to install the required dependencies:
```
apt-get update
apt-get install -y python3-cec python3-pip
pip install -r requirements.txt
```

## Usage

### Server

Execute the following command to run the server locally:

```
./cec-server.py
```

You may then go to http://127.0.0.1:8000 to browse the documentation and test the API.

The following arguments are available:

```
./cec-server.py [-h] [-a ADDRESS] [-p PORT] [-l LOG_LEVEL]

Optional arguments:
  -h, --help                           Show help message and exit
  -a ADDRESS, --address ADDRESS        Address to bind to (default: 127.0.0.1)
  -p PORT, --port PORT                 Port to listen on (default: 8000)
  -l LOG_LEVEL, --log-level LOG_LEVEL  Log level: CRITICAL, ERROR, WARNING, INFO, DEBUG (default: INFO)
```

A Docker image is also available for amd64 and arm64 architectures:

```
docker run -it --rm --device /dev/aocec -p 8000:8000 ghcr.io/fcrespel/cec-server:master [-h] [-a ADDRESS] [-p PORT] [-l LOG_LEVEL]
```

You may want to run it in the background using commands such as the following:

```
# Create and start container
docker run -d --name cec-server --device /dev/aocec -p 127.0.0.1:8000:8000 ghcr.io/fcrespel/cec-server:master

# Stop server
docker stop cec-server

# Start server
docker start cec-server

# Show live logs
docker logs -f cec-server
```

NOTE: the API port is not secured, make sure to only expose it locally or to trusted clients.

### Client

You may call the API with any HTTP client such as curl:

```
# Get TV status:
curl -sSf -XGET http://127.0.0.1:8000/device/0/status

# Power on TV:
curl -sSf -XPUT http://127.0.0.1:8000/device/0/status -d 1

# Power off TV:
curl -sSf -XPUT http://127.0.0.1:8000/device/0/status -d 0
```

Device numbers are based on the CEC protocol:
- 0: TV
- 1: Recording 1
- 2: Recording 2
- 3: Tuner 1
- 4: Playback 1
- 5: Audio system
- 6: Tuner 2
- 7: Tuner 3
- 8: Playback 2
- 9: Recording 3
- 10: Tuner 4
- 11: Playback 3
