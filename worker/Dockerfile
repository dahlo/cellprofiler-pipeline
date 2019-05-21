FROM python:3.7.2

# Set the working directory to /app
WORKDIR /app

COPY haste /app/haste
COPY setup.py /app/setup.py

RUN pip3 install /app/

# see the output more easily in k8 with -u = unbuffered
ENTRYPOINT ["python","-u","-m","haste.pipeline.worker"]