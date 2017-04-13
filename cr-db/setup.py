#!/usr/bin/env python
# coding: utf-8

from setuptools import setup, find_packages

import os
thisdir = os.path.abspath(os.path.dirname(__file__))


setup(
    name='cr.db',
    version='1.0',
    description="Crunch DB",
    author=u'Crunch.io',
    author_email='dev@crunch.io',
    license='Proprietary',
    install_requires=['pymongo'],
    tests_require=[],
    packages=find_packages(exclude=['ez_setup']),
    package_dir={'cr': 'cr'},
    package_data={'db': ['cr/db/*.json']},
    namespace_packages=['cr'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'cr.load = cr.db.loader:load_data',
        ]
    }
)
