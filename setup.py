#!/usr/bin/env python
import io
import os

from setuptools import setup

def read(file_name):
    with io.open(os.path.join(os.path.dirname(__file__), file_name), encoding='utf-8') as f:
        return f.read()

setup(
    name='phishfry',
    version="1.0.1",
    author='Cole Robinette',
    author_email='robinette.31@gmail.com',
    description='Python library and command line tool for removing/restoring emails in office365/Exchange using EWS API',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords='ews exchange microsoft outlook exchange-web-services o365 office365',
    install_requires=['requests>=2.7', 'lxml>3.0', 'requests_ntlm'],
    packages=['phishfry'],
    python_requires=">=2.7",
    zip_safe=False,
    url='https://github.com/ace-ecosystem/phishfry',
)
