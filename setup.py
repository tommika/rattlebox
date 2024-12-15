
from setuptools import setup

setup(
    name='rattlebox',
    version='0.0.1',    
    description='A GPS Toolbox',
    packages=['rattlebox'],
    install_requires=['pyserial',
                      'pydantic'
    ]
)
