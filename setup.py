
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='ener314',
    version='0.0.1',
    author='Lee Briggs',
    author_email='lee@dmzone.co.uk',
    description='Python module for Energenie raspi ENER314 adapter',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/leeb/ener314-py',
    license='GPL',
    packages=['ener314'],
    install_requires=['spidev>=3.2',
                      'RPi.GPIO>=0.6.3'])