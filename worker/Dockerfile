#FROM python:2.7.16
FROM cellprofiler/cellprofiler:3.1.8


# Set the working directory to /app
WORKDIR /app

COPY haste /app/haste
COPY setup.py /app/setup.py

RUN pip install --upgrade pip


RUN python -m pip install /app/

RUN git clone https://github.com/CellProfiler/CellProfiler-plugins.git /CellProfiler-plugins
RUN cd /CellProfiler-plugins ; pip install -r requirements.txt

RUN pip freeze

# This one seems to be missing
RUN pip install imageio

RUN pip freeze

# see the output more easily in k8 with -u = unbuffered
ENTRYPOINT ["python","-u","-m","haste.pipeline.worker"]

#CMD [ "/bin/bash" ]
