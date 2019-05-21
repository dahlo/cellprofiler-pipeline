[![Build Status](https://travis-ci.org/HASTE-project/cellprofiler-pipeline.svg?branch=master)](https://travis-ci.org/HASTE-project/cellprofiler-pipeline)



To run locally:

```

# Install:

python3 -m pip install -e ./server
python3 -m pip install -e ./client

# Start rabbitmq:
rabbitmq-server


# Start the server:
python3 -m haste.k8.server localhost

# Run the client:
python3 -m haste.k8.client localhost


```

