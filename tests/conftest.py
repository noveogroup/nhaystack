# coding: utf-8

from __future__ import absolute_import

import os


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
