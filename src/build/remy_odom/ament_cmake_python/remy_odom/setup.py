from setuptools import find_packages
from setuptools import setup

setup(
    name='remy_odom',
    version='0.0.0',
    packages=find_packages(
        include=('remy_odom', 'remy_odom.*')),
)
