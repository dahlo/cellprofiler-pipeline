#FROM python:2.7.16
FROM cellprofiler/cellprofiler:3.1.5


# Set the working directory to /app
WORKDIR /app

COPY haste /app/haste
COPY setup.py /app/setup.py

RUN python -m pip install /app/

# see the output more easily in k8 with -u = unbuffered
ENTRYPOINT ["python","-u","-m","haste.pipeline.worker"]

#CMD [ "/bin/bash" ]