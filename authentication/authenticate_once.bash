#!/bin/bash
dockerhub_image="ericstofferahn/dacqre:public"

earthengine authenticate
wait
gsutil config
cp /root/.config/earthengine/credentials /content/authentication/credentials
cp /root/.boto /content/authentication/.boto
