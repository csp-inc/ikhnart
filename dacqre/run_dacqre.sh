#!/bin/bash
dockerhub_image="registry.gitlab.com/apis-staging/dacqre"

docker run -it --rm -v $(pwd):/contents -v $(pwd)/authentication/credentials:/root/.config/earthengine/credentials -v $(pwd)/authentication/.boto:/root/.boto -w /contents $dockerhub_image python run.py
