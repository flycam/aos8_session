#!/usr/bin/env python3

from setuptools import setup

setup(
    name='aos8_session',
    py_modules=['AOS8Session'],
    version='0.6',
    description='Python module to connect to Aruba REST API for AOS 8',
    author='Stephan Westphal',
    author_email='info@stephanwestphal.com',
    url='https://github.com/flycam/aos8_session',
    install_requires=[
        'requests',
    ],
    classifiers=[
    ],
)
