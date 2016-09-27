#!/usr/bin/env python
# coding: utf-8

# n.b. we can't have unicode_literals here due to http://bugs.python.org/setuptools/issue152
from __future__ import absolute_import

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

import nhaystack

install_requires = [
    'Django>=1.6',
]

setup(
    name=nhaystack.__name__,
    version=nhaystack.__version__,
    description='Improvements, optimizations and back-ports for Haystack (with Elastic biases).',
    author=nhaystack.__author__,
    author_email='evgeny.sizikov@noveogroup.com',
    long_description=open('README.rst', 'r').read(),
    license='BSD',
    url='http://noveogroup.com/',
    packages=[
        'nhaystack',
        'nhaystack.backends',
        'nhaystack.utils',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
    ],
    zip_safe=False,
    install_requires=install_requires,
)
