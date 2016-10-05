# coding: utf-8

from __future__ import absolute_import

import os

import django


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    try:
        django.setup()
    except AttributeError:
        pass
