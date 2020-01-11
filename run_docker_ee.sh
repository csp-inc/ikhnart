#!/bin/bash
dockerhub_image="tonychangcsp/fia-cnn:latest"
PORT=8888
IP=0.0.0.0
PASSWORD=csp

nvidia-docker run -it --rm \
-p $PORT:8888 \
-e IP=$IP -e PORT=$PORT -e PASSWORD=$PASSWORD \
-v $(pwd):/contents \
-v $(pwd)/authentication/credentials:/root/.config/earthengine/credentials \
-v $(pwd)/authentication/.boto:/root/.boto \
-w /contents \
$dockerhub_image /bin/bash
