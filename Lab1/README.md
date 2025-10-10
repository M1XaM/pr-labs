# HTTP file server with TCP sockets
## Author: Isacescu Maxim FAF-231

---

## Source directory
```
LAB1
├── content // the folder which is being served
│   ├── books
│   │   └── ml-book.pdf
│   ├── index.html
│   ├── monalisa.png
│   └── pr.pdf
│
├── img // images for the report
│   └── teammate-connection.png
│
├── client.py
├── docker-compose.yml
├── Dockerfile
├── README.md  // report
└── server.py
```

## Docker & Docker Compose
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY server.py .
COPY client.py .

RUN chmod +x server.py client.py

EXPOSE 8080

CMD ["python3", "./server.py", "/app/content"]
```

```yml
services:
  http-server:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./content:/app/content:ro
    container_name: server
```
Note: There is a single server container, which also contains `client.py` in case you want to test without python access on the host.

## Quick Start
Script for starting the container: `docker compose up`   
Script that runs server with directory as an argument: `CMD ["python3", "./server.py", "/app/content"]` (from `Dockerfile`)

Content folder structure which is served:
```
content
├── books
│   └── ml-book.pdf
│
├── index.html
├── monalisa.png
└── pr.pdf
```

## Browser Requests
- Example of 404:
<img src="img/error.png" />
  
- Example of HTML with an image:
<img src="img/index.png" />
  
- Example of PDF file:
<img src="img/pdf.png" />
  
- Example of PNG file:
<img src="img/image.png" />


## Client Requests
Usage: `python client.py server_host server_port url_path directory`
Examples:
<img src="img/listening-root.png" />
<img src="img/index-in-terminal.png" />
<img src="img/save-pdf.png" />


## Subdirectory
<img src="img/subdirectory.png" />
  

## Friend's Server
My IP:
<img src="img/my-ip.png" />

The setup:
<img src="img/setup.png" />

The result:
<img src="img/teammate-connection.png" />
