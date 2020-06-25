IMAGE_NAME=cspinc/ikhnart:latest
DATADRIVE=/datadrive
docker run -it \
	-p 8080:8080 \
	-v $(pwd):/content \
	-v $DATADRIVE:$DATADRIVE \
	-w /content \
	-v $(pwd)/authentication/credentials:/root/.config/earthengine/credentials \
	-v $(pwd)/authentication/.boto:/root/.boto \
	--rm \
	$IMAGE_NAME \
	jupyter notebook --port 8080 --ip 0.0.0.0 --no-browser --allow-root

