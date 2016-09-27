# coding: utf-8

from __future__ import absolute_import

from optparse import make_option
from itertools import count

from django.core.management.base import BaseCommand
from django.core.management import call_command

from elasticsearch.helpers import reindex
from haystack import connections

__all__ = ['Command']


class HaystackElasticsearchCommandMixin:
    INDEX_TEMPLATE = '{}_v{}'

    def format_index_name(self, index_name, version=0):
        return self.INDEX_TEMPLATE.format(index_name, version)

    def alias_exists(self, index_alias):
        backend = self.backend
        return backend.conn.indices.exists_alias(name=index_alias)

    def index_exists(self, index_name):
        backend = self.backend
        return backend.conn.indices.exists(index_name)

    def create_alias(self, index_name, index_alias):
        backend = self.backend
        return backend.conn.indices.put_alias(index=index_name, name=index_alias)

    def delete_alias(self, index_name, index_alias='_all'):
        backend = self.backend
        return backend.conn.indices.delete_alias(index_name, name=index_alias)

    def update_alias(self, old_index_name, new_index_name, index_alias):
        backend = self.backend
        update_aliases = {
            'actions': [
                {'remove': {'index': old_index_name,
                            'alias': index_alias}},
                {'add': {'index': new_index_name,
                         'alias': index_alias}}
            ]
        }
        return backend.conn.indices.update_aliases(body=update_aliases)

    def reindex_index(self, old_index_name, new_index_name):
        backend = self.backend
        return reindex(backend.conn, old_index_name, new_index_name)

    def create_index(self, index_name):
        backend = self.backend
        backend.index_name = index_name
        if self.commit:
            backend.setup()
        if self.verbosity >= 1:
            self.stdout.write('Created a new index {}'.format(index_name))

    def clear_index(self, index_name):
        backend = self.backend
        if self.commit:
            backend.index_name = index_name
            backend.clear()
        if self.verbosity >= 1:
            self.stdout.write('Removed obsolete index {}'.format(index_name))


class Command(HaystackElasticsearchCommandMixin, BaseCommand):
    help = """Completely rebuilds the search index by creating a new versioned index
 (starts with <index>_v0), copying all data from the old index <index> into
 the new <index_v0>, and creating an index alias <index> for the new versioned
 index <index_v0>."""

    base_options = (
        make_option(
            '--noinput', action='store_false', dest='interactive', default=True,
            help='If provided, no prompts will be issued to the user and the data will be wiped out.'
        ),
        make_option(
            '-u', '--using', action='append', dest='using',
            default=[],
            help='Update only the named backend (can be used multiple times). '
                 'By default all backends will be updated.'
        ),
        make_option(
            '--nocommit', action='store_false', dest='commit',
            default=True, help='Will pass commit=False to the backend.'
        ),
    )
    option_list = BaseCommand.option_list + base_options

    def handle(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.commit = options.get('commit', True)

        using = options.get('using')
        if not using:
            using = connections.connections_info.keys()

        for backend_name in using:
            self.backend = backend = connections[backend_name].get_backend()

            # use the configured INDEX_NAME as the alias name
            index_alias = backend.index_name
            old_index_name, new_index_name = tuple(self.prepare_index_names(index_alias))

            if old_index_name is None:
                if self.index_exists(index_alias):
                    self.reindex_index(index_alias, new_index_name)
                else:
                    self.create_index(new_index_name)

                    if self.commit:
                        call_command('update_index', **options)
                    if self.verbosity >= 1:
                        self.stdout.write('Finished updating initial index {} aliased as {}'.format(
                            new_index_name, index_alias
                        ))

                if self.commit:
                    self.create_alias(new_index_name, index_alias)
                if self.verbosity >= 1:
                    self.stdout.write('Created a new alias {} for the new index {}'.format(index_alias, new_index_name))
            else:
                self.reindex_index(old_index_name, new_index_name, index_alias=index_alias)

        if self.verbosity >= 1:
            self.stdout.write("All documents have been re-indexed.")

    def reindex_index(self, old_index_name, new_index_name, index_alias=None):
        self.create_index(new_index_name)

        if self.commit:
            super(Command, self).reindex_index(old_index_name, new_index_name)
            if index_alias is not None:
                self.update_alias(old_index_name, new_index_name, index_alias)
        if self.verbosity >= 1:
            self.stdout.write('Finished reindexing from {} to {}{}'.format(
                old_index_name, new_index_name,
                ' aliased as {}'.format(index_alias) if index_alias else ''
            ))

        self.clear_index(old_index_name)

    def prepare_index_names(self, index_name):
        version = count()

        # detect source version
        if not self.alias_exists(index_name):
            # no alises have been found for the index
            yield None
        else:
            while True:
                index_version = self.format_index_name(index_name, next(version))
                if self.index_exists(index_version):
                    yield index_version
                    break

        # detect target version
        while True:
            index_version = self.format_index_name(index_name, next(version))
            if not self.index_exists(index_version):
                yield index_version
                break
