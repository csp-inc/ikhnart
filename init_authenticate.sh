#!/bin/bash
dockerhub_image="registry.gitlab.com/apis-staging/dacqre"

docker run -it --rm -v $(pwd):/content -w /content $dockerhub_image ./authentication/authenticate_once.bash
