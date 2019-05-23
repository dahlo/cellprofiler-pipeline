#!/usr/bin/env bash


#python2 -m cellprofiler -c  \
#--plugins-directory ~/projects/haste/CellProfiler-plugins \
#-p /Users/benblamey/projects/haste/cell-profiler-work/OutOfFocus-TestImages.cppipe \
#--data-file /Users/benblamey/projects/haste/cell-profiler-work/file-list.csv


python2 -m cellprofiler -c  \
--plugins-directory ~/projects/haste/CellProfiler-plugins \
-p /Users/benblamey/projects/haste/cell-profiler-work/OutOfFocus-TestImages.cppipe \
--file-list /Users/benblamey/projects/haste/cell-profiler-work/file-list.txt \
-o .