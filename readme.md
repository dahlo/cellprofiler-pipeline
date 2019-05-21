[![Build Status](https://travis-ci.org/HASTE-project/cellprofiler-pipeline.svg?branch=master)](https://travis-ci.org/HASTE-project/cellprofiler-pipeline)



To run locally:

```

# Install:

python3 -m pip install -e ./worker
python3 -m pip install -e ./client

# Start rabbitmq:
rabbitmq-server

# Start the worker:
python3 -m haste.pipeline.worker --host localhost /foo

# Start the client:
python3 -m haste.pipeline.client --include png --tag foo --host localhost /foo


```


To run locally, with containers:

```
docker build --no-cache=true -t "benblamey/haste_pipeline_client:latest" ./client
docker run benblamey/haste_pipeline_client:latest --include png --tag foo --host localhost /foo

...
```