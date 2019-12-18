IMAGE_NAME=tonychangcsp/ikhnart:latest
docker run -it \
	-p 8080:8080 \
	-v $(pwd):/content \
	-w /content \
	--rm \
	$IMAGE_NAME \
	jupyter notebook --port 8080 --ip 0.0.0.0 --no-browser --allow-root

