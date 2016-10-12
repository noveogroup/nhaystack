
=========
nhaystack
=========

:Version: 0.0.2
:Author: Noveo Group (http://noveogroup.com/)

Improvements, optimizations and back-ports for Haystack (with Elastic biases).

Build status
============

.. image:: https://travis-ci.org/noveogroup/nhaystack.svg?branch=master
    target: https://travis-ci.org/noveogroup/nhaystack.svg

Requirements
============

* `Django <https://www.djangoproject.com/>`_: targeting LTS releases (1.6, 1.8),
  tested against 1.6.11 only at the moment.
* `Haystack <http://www.haystacksearch.org/>`_: tested against 2.4.1
* `Elastic <http://www.elasticsearch.org/>`_: tested against 1.7.0
* `elasticsearch-py <http://www.elasticsearch.org/>`_: tested against 1.9.0
* `elasticstack <https://pypi.python.org/pypi/elasticstack/>`_: tested against 0.4.1

Features and goals
==================

TODO

Why not just add stuff to upstream (Haystack or Elasticstack)?
--------------------------------------------------------------

This project aims to solve problems and reuse code patterns between Noveo Group
projects. Parts of this work, once finalized, tested and proven, may become
suitable to be pushed to upstream.
