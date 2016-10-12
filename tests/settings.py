# coding: utf-8

from __future__ import absolute_import

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def local_path(*args):
    return os.path.join(BASE_DIR, os.path.join(*args))

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': local_path('db.sqlite3'),
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
            ],
        },
    },
]

SECRET_KEY = 'ii4sjhh)!%m_7=$lqpc(w#dvl^v&&g&gf!y2go)7k25%0v699='

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

USE_I18N = False

# Application definition

INSTALLED_APPS = [
    'elasticstack',
    'haystack',
    'tests.music',
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'nhaystack.backends.elasticsearch.ElasticsearchSearchEngine',
        'URL': 'http://localhost:9200',
        'INDEX_NAME': 'nhaystack'
    },
}
HAYSTACK_SIGNAL_PROCESSOR = 'tests.search.RealtimeModelSignalProcessor'
