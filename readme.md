[![Build Status](https://travis-ci.org/HASTE-project/cellprofiler-pipeline.svg?branch=master)](https://travis-ci.org/HASTE-project/cellprofiler-pipeline)



To run locally (for development):

```

# Install:

python2 -m pip install --user -e ./worker
python3 -m pip install -e ./client

# Start rabbitmq:
rabbitmq-server

rabbitmqadmin delete queue name='files'

# Start the worker:
python2 -m haste.pipeline.worker --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images/target

# Start the client:
python3 -m haste.pipeline.client --include png --tag foo --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images/target

# Stop rabbitmq
rabbitmqctl stop

```


To run locally, with containers:

```
docker build --no-cache=true -t "benblamey/haste_pipeline_client:latest" ./client
docker run benblamey/haste_pipeline_client:latest --include png --tag foo --host localhost /Users/benblamey/projects/haste/haste-desktop-agent-images

docker build -t "benblamey/haste_pipeline_worker:latest" ./worker
docker push "benblamey/haste_pipeline_worker:latest"




# run cellprofiler to test ('dry-run')
docker run -it --entrypoint=/bin/bash benblamey/haste_pipeline_worker:latest -i 
# then...
python2 -m cellprofiler -c  \
--plugins-directory /CellProfiler-plugins \
-p ../dry-run/OutOfFocus-TestImages.cppipe \
--file-list /dry-run/file-list.txt \
-o .










# run python script, with dev default config:
docker run benblamey/haste_pipeline_worker:latest


```
Note: this will take a bit of RAM.
If you see complaints on memory then "Killed", bump the mem allowed by docker, and restart.

