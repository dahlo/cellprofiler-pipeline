#!/usr/bin/env python

from setuptools import setup

setup(name='haste_pipeline_worker',
      version='0.10',
      packages=['haste.pipeline.worker'],
      namespace_packages=[
          'haste',
          'haste.pipeline'
      ],
      author='Ben Blamey',
      author_email='ben.blamey@it.uu.se',
      install_requires=[
          'pika'
      ],
      test_requires=[
          'pytest'
      ]
      )
