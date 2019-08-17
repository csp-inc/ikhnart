nvidia-docker run -it -p 8080:8080 -v $(pwd):/content -v /E:/E -w /content --rm tonychangcsp/keras:v1.1 jupyter notebook --port 8080 --ip 0.0.0.0 --no-browser --allow-root

