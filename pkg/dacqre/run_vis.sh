#!/bin/bash
dockerhub_image="registry.gitlab.com/apis-staging/dacqre"

docker run -it --rm -v $(pwd):/contents -w /contents $dockerhub_image python run-vis.py
