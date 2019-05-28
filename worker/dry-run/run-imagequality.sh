pip freeze

python2 -m cellprofiler -c  \
--plugins-directory /CellProfiler-plugins \
-p ../dry-run/MeasureImageQuality-TestImages.cppipe \
--file-list /dry-run/file-list.txt \
-o .
