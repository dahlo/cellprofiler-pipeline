
#!/usr/bin/env bash

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

#docker push benblamey/haste_pipeline_worker_base:latest
docker push benblamey/haste_pipeline_worker:latest
docker push benblamey/haste_pipeline_client:latest
