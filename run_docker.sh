IMAGE_NAME=cspinc/ikhnart:latest
docker run -it \
	-p 8080:8080 \
	-v $(pwd):/content \
	-v /datadrive:/datadrive \
	-w /content \
	--rm \
	$IMAGE_NAME \
	/bin/bash

