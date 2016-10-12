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

setup_requires = [
    'pytest-runner',
]

tests_requires = [
    'django-haystack==2.4.1',
    'elasticsearch>=1.0.0,<2.0.0',
    'elasticstack==0.4.1',
    'whoosh>=2.5.0',

    'pytest<2.9.0',
    'pytest_django<3.0.0',
]

setup(
    name=nhaystack.__name__,
    version=nhaystack.__version__,
    description='Improvements, optimizations and back-ports for Haystack (with Elastic biases).',
    author=nhaystack.__author__,
    author_email='evgeny.sizikov@noveogroup.com',
    long_description=open('README.rst', 'r').read(),
    license='BSD',
    url='https://github.com/noveogroup/nhaystack',
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
    zip_safe=True,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_requires,
)
