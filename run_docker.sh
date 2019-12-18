IMAGE_NAME=tonychangcsp/ikhnart:latest
docker run -it \
	-p 8080:8080 \
	-v $(pwd):/content \
	-w /content \
	--rm \
	$IMAGE_NAME \
	/bin/bash

