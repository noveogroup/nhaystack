# coding: utf-8

from __future__ import absolute_import

import os

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

DEFAULT_ENV = 'HAYSTACK_CONNECTION_URL'

SCHEMES = {
    'solr': 'haystack.backends.solr_backend.SolrEngine',
    'elastic': 'nhaystack.backends.elasticsearch.ElasticsearchSearchEngine',
    'whoosh': 'nhaystack.backends.whoosh.WhooshEngine',
    'xapian': 'xapian_backend.XapianEngine',
    'simple': 'haystack.backends.simple_backend.SimpleEngine',
}
# Register connection schemes in URLs.
for scheme in SCHEMES:
    urlparse.uses_netloc.append(scheme)


def config(env=DEFAULT_ENV, default=None, engine=None, **configs):
    """Returns configured HAYSTACK_CONNECTION dictionary from HAYSTACK_CONNECTION_URL."""

    s = os.getenv(env, default)
    if s:
        _config = parse(s, engine)
        _config.update(configs)
        return _config

    return configs


def parse(url, engine=None):
    """Parses a connection URL."""

    _config = {}

    url = urlparse.urlparse(url)
    # Split query strings from path.
    path = url.path[1:]
    if '?' in path and not url.query:
        path, query = path.split('?', 2)
    else:
        path, query = path, url.query

    # Lookup specified engine
    _config['ENGINE'] = engine or SCHEMES[url.scheme]

    if url.scheme == 'elastic':
        _config['URL'] = url.netloc
        _config['INDEX_NAME'] = path or ''
    elif url.scheme == 'whoosh':
        _config['PATH'] = os.path.join(url.netloc, path)
    elif url.scheme == 'xapian':
        _config['PATH'] = os.path.join(url.netloc, path)
    elif url.scheme == 'solr':
        _config['URL'] = ''.join([url.netloc, path])

    _config.update(urlparse.parse_qs(query))
    return _config
