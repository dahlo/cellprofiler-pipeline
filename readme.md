[![Build Status](https://travis-ci.org/HASTE-project/cellprofiler-pipeline.svg?branch=master)](https://travis-ci.org/HASTE-project/cellprofiler-pipeline)



To run locally (for development):

```

# Install:

python3 -m pip install -e ./worker
python3 -m pip install -e ./client

# Start rabbitmq:
rabbitmq-server

# Start the worker:
python3 -m haste.pipeline.worker --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images/target

# Start the client:
python3 -m haste.pipeline.client --include png --tag foo --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images/target


```


To run locally, with containers:

```
docker build --no-cache=true -t "benblamey/haste_pipeline_client:latest" ./client
docker build --no-cache=true -t "benblamey/haste_pipeline_worker:latest" ./client
docker run benblamey/haste_pipeline_client:latest --include png --tag foo --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images
docker run benblamey/haste_pipeline_worker:latest --tag foo --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images
...
```
