# coding: utf-8

from __future__ import absolute_import

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import haystack
from haystack.backends import elasticsearch_backend
from haystack.backends.elasticsearch_backend import bulk
from haystack.constants import ID
from haystack.exceptions import SkipDocument
from haystack.inputs import Raw
from haystack.utils import get_identifier

import elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError

from elasticstack.backends import ConfigurableElasticBackend, ConfigurableElasticSearchEngine

ELASTICSEARCH_ID = '_id'
TRUE = 'true'
FALSE = 'false'
NULL = 'null'


class Boolean(Raw):
    input_type_name = 'boolean'

    def prepare(self, query_obj):
        return TRUE if self.query_string else FALSE


class ElasticsearchSearchBackend(ConfigurableElasticBackend):
    def __init__(self, connection_alias, **connection_options):
        super(ElasticsearchSearchBackend, self).__init__(connection_alias, **connection_options)
        # adding user field mappings
        global_field_mappings = getattr(settings, 'ELASTICSEARCH_FIELD_MAPPINGS', None)
        connection_field_mappings = connection_options.get('FIELD_MAPPINGS', None)
        if global_field_mappings and connection_field_mappings:
            raise ImproperlyConfigured("You cannot specify ELASTICSEARCH_FIELD_MAPPINGS in settings "
                                       "and also 'FIELD_MAPPINGS' in your index connection '%s'. "
                                       "Use only one configuration way." % connection_alias)
        user_field_mapping = connection_field_mappings or global_field_mappings
        if user_field_mapping:
            setattr(elasticsearch_backend, 'FIELD_MAPPINGS', user_field_mapping)
        # end adding user field mappings

    def setup(self):
        """
        Defers loading until needed.
        """
        # Get the existing mapping & cache it. We'll compare it
        # during the ``update`` & if it doesn't match, we'll put the new
        # mapping.
        try:
            self.existing_mapping = self.conn.indices.get_mapping(index=self.index_name)
        except NotFoundError:
            pass
        except Exception:
            if not self.silently_fail:
                raise

        unified_index = haystack.connections[self.connection_alias].get_unified_index()
        self.content_field_name, field_mapping = self.build_schema(unified_index.all_searchfields())
        # fixing ES 1.x/2.x compatible `_boost`
        current_mapping = {
            'modelresult': {
                'properties': field_mapping,
            }
        }
        if elasticsearch.VERSION < (2, 0, 0):
            current_mapping['modelresult']['_boost'] = {
                'name': 'boost',
                'null_value': 1.0
            }
        # end fixing ES 1.x/2.x compatible `_boost`

        if current_mapping != self.existing_mapping:
            try:
                # Make sure the index is there first.
                self.conn.indices.create(index=self.index_name, body=self.DEFAULT_SETTINGS, ignore=400)
                self.conn.indices.put_mapping(index=self.index_name, doc_type='modelresult', body=current_mapping)
                self.existing_mapping = current_mapping
            except Exception:
                if not self.silently_fail:
                    raise

        self.setup_complete = True

    def update(self, index, iterable, commit=True):
        if not self.setup_complete:
            try:
                self.setup()
            except TransportError as e:
                if not self.silently_fail:
                    raise

                self.log.error(u"Failed to add documents to Elasticsearch: %s", e, exc_info=True)
                return

        prepped_docs = []

        for obj in iterable:
            try:
                prepped_data = index.full_prepare(obj)
                # removing 'id' item from data
                # Convert the data to make sure it's happy.
                final_data = {
                    ELASTICSEARCH_ID if key == ID else key: self._from_python(value)
                    for key, value in prepped_data.items()
                }
                # end removing 'id' item from data

                prepped_docs.append(final_data)
            except SkipDocument:
                self.log.debug(u"Indexing for object `%s` skipped", obj)
            except TransportError as e:
                if not self.silently_fail:
                    raise

                # We'll log the object identifier but won't include the actual object
                # to avoid the possibility of that generating encoding errors while
                # processing the log message:
                self.log.error(u"%s while preparing object for update" % e.__class__.__name__, exc_info=True,
                               extra={"data": {"index": index,
                                               "object": get_identifier(obj)}})

        bulk(self.conn, prepped_docs, index=self.index_name, doc_type='modelresult')

        if commit:
            self.conn.indices.refresh(index=self.index_name)


class ElasticsearchSearchQuery(elasticsearch_backend.ElasticsearchSearchQuery):
    def build_query_fragment(self, field, filter_type, value):
        # handling 'boolean' fields and 'null' value
        if not (hasattr(value, 'input_type_name') or hasattr(value, 'values_list')):
            if isinstance(value, bool):
                value = Boolean(value)
            elif value is None:
                value = Raw(NULL)
        # end handling 'boolean' fields and 'null' value
        return super(ElasticsearchSearchQuery, self).build_query_fragment(field, filter_type, value)


class ElasticsearchSearchEngine(ConfigurableElasticSearchEngine):
    backend = ElasticsearchSearchBackend
    query = ElasticsearchSearchQuery
