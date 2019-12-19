#!/bin/bash
IMAGE_NAME=tonychangcsp/ikhnart:latest

if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
    docker build -t $IMAGE_NAME -f ./docker/Dockerfile .
else
    echo "$IMAGE_NAME exists locally!"
fi

