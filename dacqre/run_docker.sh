#!/bin/bash
dockerhub_image="registry.gitlab.com/apis-staging/dacqre"

if [[ -z "$1" ]]; then
    DATADRIVE=$(pwd)/collections
else
    DATADRIVE=$1
fi

docker run -it --rm \
    -v $DATADRIVE:/datadrive \
    -v $(pwd):/contents \
    -v $(pwd)/authentication/credentials:/root/.config/earthengine/credentials \
    -v $(pwd)/authentication/.boto:/root/.boto \
    -w /contents $dockerhub_image \
    /bin/bash
