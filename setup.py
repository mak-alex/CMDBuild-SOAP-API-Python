#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name     = 'cmdbuild-soap-api',
    version  = '0.1.0',
    packages = find_packages(),
    requires = ['python (>= 2.5)'],
    description  = 'CMDBuild SOAP API Module',
    long_description = open('README.markdown').read(),
    author       = 'Alexandr Mikhailenko a.k.a Alex M.A.K.',
    author_email = 'alex-m.a.k@yandex.kz',
    url          = 'https://bitbucket.org/enlab/cmdbuild_soap_api_python',
    download_url = 'https://bitbucket.org/enlab/cmdbuild_soap_api_python/get/master.tar.gz',
    license      = 'MIT License',
    keywords     = ['cmdbuild','soap','api','cmdbuild api','cmdbuild soap','cmdbuild soap api'],
    classifiers  = [
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
    ],
    install_requires=[
          'suds',
          'suds-py3-fixes'
    ],
)

