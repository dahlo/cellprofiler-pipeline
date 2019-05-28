FROM benblamey/haste_pipeline_worker_base:latest

#WORKDIR /
#RUN cd /CellProfiler-plugins ; pip install -r requirements.txt


# Set the working directory to /app
WORKDIR /app

COPY haste /app/haste
COPY setup.py /app/setup.py
RUN python -m pip install /app/

COPY dry-run /dry-run

# This one seems to be missing
#RUN pip install imageio
#RUN pip install statistics
#RUN pip install pyjnius
RUN pip install h5py --upgrade

# /CellProfiler-plugins/runimagej.py seems to need an old versin of imagej
#RUN pip install imagej==0.1.1


RUN pip freeze

# For testing deps etc.
#CMD python2 -m cellprofiler -c  \
#    --plugins-directory /CellProfiler-plugins \
#    -p ../dry-run/MeasureImageQuality-TestImages.cppipe \
#    --file-list /dry-run/file-list.txt \
#    -o .

# see the output more easily in k8 with -u = unbuffered#
ENTRYPOINT ["python","-u","-m","haste.pipeline.worker"]
