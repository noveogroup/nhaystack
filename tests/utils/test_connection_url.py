# coding: utf-8

from __future__ import absolute_import

import os

from nhaystack.utils import connection_url


def test_empty_config():
    config = connection_url.config()
    assert config == {}

def test_extra_args_config():
    config = connection_url.config(EXTRA_ONE='test', EXTRA_TWO=[], EXTRA_THREE={})
    assert config == {'EXTRA_ONE': 'test', 'EXTRA_TWO': [], 'EXTRA_THREE': {}}

def test_default_env_simple_config():
    os.environ[connection_url.DEFAULT_ENV] = 'simple://test:0000/test?test=test'
    config = connection_url.config()
    try:
        assert config == {'ENGINE': 'haystack.backends.simple_backend.SimpleEngine', 'test': ['test']}
    finally:
        del os.environ[connection_url.DEFAULT_ENV]

def test_default_env_elastic_config():
    os.environ[connection_url.DEFAULT_ENV] = 'elastic://test:9200/test?test=test1&test=test2&test2=test'
    config = connection_url.config()
    try:
        assert config == {
            'ENGINE': 'nhaystack.backends.elasticsearch.ElasticsearchSearchEngine',
            'INDEX_NAME': 'test',
            'URL': 'test:9200',
            'test': ['test1', 'test2'],
            'test2': ['test'],
        }
    finally:
        del os.environ[connection_url.DEFAULT_ENV]

def test_default_env_whoosh_config():
    os.environ[connection_url.DEFAULT_ENV] = 'whoosh://test_whoosh/test?test=test1&test=test2&test2=test'
    config = connection_url.config()
    try:
        assert config == {
            'ENGINE': 'nhaystack.backends.whoosh.WhooshEngine',
            'PATH': 'test_whoosh/test',
            'test': ['test1', 'test2'],
            'test2': ['test'],
        }
    finally:
        del os.environ[connection_url.DEFAULT_ENV]

def test_default_env_xapian_config():
    os.environ[connection_url.DEFAULT_ENV] = 'xapian://test_xapian/test?test=test1&test=test2&test2=test'
    config = connection_url.config()
    try:
        assert config == {
            'ENGINE': 'xapian_backend.XapianEngine',
            'PATH': 'test_xapian/test',
            'test': ['test1', 'test2'],
            'test2': ['test'],
        }
    finally:
        del os.environ[connection_url.DEFAULT_ENV]

def test_default_simple_config():
    config = connection_url.config(default='simple://test:0000/test?test=test')
    assert config == {'ENGINE': 'haystack.backends.simple_backend.SimpleEngine', 'test': ['test']}

def test_default_elastic_config():
    config = connection_url.config(default='elastic://test:9200/test?test=test1&test=test2&test2=test')
    assert config == {
        'ENGINE': 'nhaystack.backends.elasticsearch.ElasticsearchSearchEngine',
        'INDEX_NAME': 'test',
        'URL': 'test:9200',
        'test': ['test1', 'test2'],
        'test2': ['test'],
    }

def test_default_whoosh_config():
    config = connection_url.config(default='whoosh://test_whoosh/test?test=test1&test=test2&test2=test')
    assert config == {
        'ENGINE': 'nhaystack.backends.whoosh.WhooshEngine',
        'PATH': 'test_whoosh/test',
        'test': ['test1', 'test2'],
        'test2': ['test'],
    }

def test_default_xapian_config():
    config = connection_url.config(default='xapian://test_xapian/test?test=test1&test=test2&test2=test')
    assert config == {
        'ENGINE': 'xapian_backend.XapianEngine',
        'PATH': 'test_xapian/test',
        'test': ['test1', 'test2'],
        'test2': ['test'],
    }

def test_default_engine_simple_config():
    config = connection_url.config(
        default='simple://test:0000/test?test=test',
        engine='backends.SimpleEngine',
    )
    assert config == {'ENGINE': 'backends.SimpleEngine', 'test': ['test']}

def test_default_engine_elastic_config():
    config = connection_url.config(
        default='elastic://test:9200/test?test=test1&test=test2&test2=test',
        engine='backends.ElasticsearchSearchEngine',
    )
    assert config == {
        'ENGINE': 'backends.ElasticsearchSearchEngine',
        'INDEX_NAME': 'test',
        'URL': 'test:9200',
        'test': ['test1', 'test2'],
        'test2': ['test'],
    }

def test_default_engine_whoosh_config():
    config = connection_url.config(
        default='whoosh://test_whoosh/test?test=test1&test=test2&test2=test',
        engine='backends.WhooshEngine',
    )
    assert config == {
        'ENGINE': 'backends.WhooshEngine',
        'PATH': 'test_whoosh/test',
        'test': ['test1', 'test2'],
        'test2': ['test'],
    }

def test_default_engine_xapian_config():
    config = connection_url.config(
        default='xapian://test_xapian/test?test=test1&test=test2&test2=test',
        engine='backends.XapianEngine',
    )
    assert config == {
        'ENGINE': 'backends.XapianEngine',
        'PATH': 'test_xapian/test',
        'test': ['test1', 'test2'],
        'test2': ['test'],
    }
