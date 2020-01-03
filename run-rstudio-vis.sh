#!/usr/bin/env bash
DATA_DIR = data
IMAGE = cspinc/apis-staging/greenwave:geospatial-vis
echo http://localhost:8789/
rm -rf .rstudio/
docker run -it --rm \
    -v "$(pwd)":/home/gw-cpu \
    -v "$(pwd)/$DATA_DIR":/data \
    -e USER=gw-cpu \
    -e PASSWORD=gw-cpu \
    -p 8789:8787 \
    $IMAGE \
    rm -rf kitematic/
