# coding: utf-8

from __future__ import absolute_import

import warnings
from contextlib import closing
from functools import wraps

from django.conf import settings
from django.utils import six
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

from haystack import connections
from haystack.backends import log_query, whoosh_backend
from haystack.backends.whoosh_backend import WhooshHtmlFormatter
from haystack.constants import ID, DJANGO_CT, DJANGO_ID
from haystack.exceptions import SearchBackendError
from haystack.models import SearchResult
from haystack.utils import get_model_ct
from haystack.utils.app_loading import haystack_get_model
from haystack.utils.loading import import_class

# Bubble up the correct error.
from whoosh.analysis.analyzers import StemmingAnalyzer
from whoosh.analysis.filters import CharsetFilter, LowercaseFilter, StopFilter, Filter
from whoosh.analysis.morph import StemFilter
from whoosh.analysis.tokenizers import RegexTokenizer
from whoosh.fields import ID as WHOOSH_ID
from whoosh.fields import Schema, IDLIST, TEXT, KEYWORD, NUMERIC, BOOLEAN, DATETIME, NGRAM, NGRAMWORDS
from whoosh.highlight import highlight as whoosh_highlight, ContextFragmenter
from whoosh.lang import NoStemmer, NoStopWords
from whoosh.sorting import FacetType, ScoreFacet, FieldFacet, MultiFacet
from whoosh.support.charset import accent_map


class EmptyResults(Exception):
    def __init__(self, **kwargs):
        self._kwargs = kwargs


def empty_results(decorated_func):
    @wraps
    def wrapper(*args, **kwargs):
        try:
            return decorated_func(*args, **kwargs)
        except EmptyResults as exc:
            result = {
                'results': [],
                'hits': 0,
                'facets': {},
                'spelling_suggestion': None,
            }
            result.update(exc._kwargs)
            return result
    return wrapper


class DecodeFilter(Filter):
    def __init__(self, encoding='ascii'):
        self.encoding = encoding

    def __call__(self, tokens):
        assert hasattr(tokens, '__iter__')
        for t in tokens:
            t.text = t.text.encode(self.encoding, 'ignore')
            yield t


def LanguageAnalyzer(lang, cachesize=50000, **tokenizer_kwargs):
    # Make the start of the chain
    chain = (RegexTokenizer(**tokenizer_kwargs) | LowercaseFilter())

    # Add a stop word filter
    try:
        chain = chain | StopFilter(lang=lang)
    except NoStopWords:
        pass

    # Add accent folding and convert to ASCII
    chain = chain | CharsetFilter(accent_map) | DecodeFilter()

    # Add a stemming filter
    try:
        chain = chain | StemFilter(lang=lang, cachesize=cachesize)
    except NoStemmer:
        pass

    return chain


class WhooshSearchBackend(whoosh_backend.WhooshSearchBackend):
    def __init__(self, connection_alias, **connection_options):
        super(WhooshSearchBackend, self).__init__(connection_alias, **connection_options)
        default_analyzer = connection_options.get('DEFAULT_ANALYZER')
        if default_analyzer:
            default_analyzer_class = connection_options.get('DEFAULT_ANALYZER_CLASS')
            if default_analyzer_class:
                default_analyzer_class = import_class(default_analyzer_class)
            else:
                default_analyzer_class = LanguageAnalyzer
            self.analyzer = default_analyzer_class(default_analyzer)
        else:
            self.analyzer = StemmingAnalyzer()

    def build_schema(self, fields):
        schema_fields = {
            ID: WHOOSH_ID(stored=True, unique=True),
            DJANGO_CT: WHOOSH_ID(stored=True, sortable=True),  # required for ordering by model content type
            DJANGO_ID: WHOOSH_ID(stored=True),
        }
        # Grab the number of keys that are hard-coded into Haystack.
        # We'll use this to (possibly) fail slightly more gracefully later.
        initial_key_count = len(schema_fields)
        content_field_name = ''

        for field_class in six.itervalues(fields):
            if field_class.is_multivalued:
                if field_class.indexed is False:
                    schema_fields[field_class.index_fieldname] = IDLIST(stored=True, field_boost=field_class.boost)
                else:
                    schema_fields[field_class.index_fieldname] = KEYWORD(stored=True, commas=True, scorable=True,
                                                                         field_boost=field_class.boost)
            elif field_class.field_type in ['date', 'datetime']:
                schema_fields[field_class.index_fieldname] = DATETIME(stored=field_class.stored, sortable=True)
            elif field_class.field_type == 'integer':
                schema_fields[field_class.index_fieldname] = NUMERIC(stored=field_class.stored, numtype=int,
                                                                     field_boost=field_class.boost)
            elif field_class.field_type == 'float':
                schema_fields[field_class.index_fieldname] = NUMERIC(stored=field_class.stored, numtype=float,
                                                                     field_boost=field_class.boost)
            elif field_class.field_type == 'boolean':
                # Field boost isn't supported on BOOLEAN as of 1.8.2.
                schema_fields[field_class.index_fieldname] = BOOLEAN(stored=field_class.stored)
            elif field_class.field_type == 'ngram':
                schema_fields[field_class.index_fieldname] = NGRAM(minsize=3, maxsize=15, stored=field_class.stored,
                                                                   field_boost=field_class.boost)
            elif field_class.field_type == 'edge_ngram':
                schema_fields[field_class.index_fieldname] = NGRAMWORDS(minsize=2, maxsize=15, at='start',
                                                                        stored=field_class.stored,
                                                                        field_boost=field_class.boost)
            else:
                schema_fields[field_class.index_fieldname] = TEXT(stored=True, analyzer=self.analyzer,
                                                                  field_boost=field_class.boost, sortable=True)

            if field_class.document is True:
                content_field_name = field_class.index_fieldname
                schema_fields[field_class.index_fieldname].spelling = True

        # Fail more gracefully than relying on the backend to die if no fields
        # are found.
        if len(schema_fields) <= initial_key_count:
            raise SearchBackendError("No fields were found in any search_indexes. "
                                     "Please correct this before attempting to search.")

        return (content_field_name, Schema(**schema_fields))

    @log_query
    @empty_results
    def search(self, query_string, sort_by=None, start_offset=0, end_offset=None,
               fields='', highlight=False, facets=None, date_facets=None, query_facets=None,
               narrow_queries=None, spelling_query=None, within=None,
               dwithin=None, distance_point=None, models=None,
               limit_to_registered_models=None, result_class=None, **kwargs):
        if not self.setup_complete:
            self.setup()

        # A zero length query should return no results.
        if not len(query_string):
            raise EmptyResults

        query_string = force_text(query_string)

        # A one-character query (non-wildcard) gets nabbed by a stopwords
        # filter and should yield zero results.
        if len(query_string) <= 1 and query_string != u'*':
            raise EmptyResults

        if facets is not None:
            warnings.warn("Whoosh does not handle faceting.", Warning, stacklevel=2)

        if date_facets is not None:
            warnings.warn("Whoosh does not handle date faceting.", Warning, stacklevel=2)

        if query_facets is not None:
            warnings.warn("Whoosh does not handle query faceting.", Warning, stacklevel=2)

        self.index = self.index.refresh()

        if self.index.doc_count():
            parsed_query = self.parser.parse(query_string)

            # In the event of an invalid/stopworded query, recover gracefully.
            if not parsed_query:
                raise EmptyResults

            page_num, page_length = self.calculate_page(start_offset, end_offset)

            search_kwargs = {
                'pagelen': page_length,
                'sortedby': self._sort_by(sort_by),
            }

            # Handle the case where the results have been narrowed.
            narrowed_results = self._narrow(narrow_queries,
                                            models, limit_to_registered_models)
            if narrowed_results is not None:
                search_kwargs['filter'] = narrowed_results

            searcher = self.index.searcher()
            with closing(searcher):
                try:
                    raw_page = searcher.search_page(
                        parsed_query,
                        page_num,
                        **search_kwargs
                    )
                except ValueError:
                    if not self.silently_fail:
                        raise

                    raise EmptyResults
                else:
                    # Because as of Whoosh 2.5.1, it will return the wrong page of
                    # results if you request something too high. :(
                    if raw_page.pagenum < page_num:
                        raise EmptyResults

                    return self._process_results(raw_page, highlight=highlight, query_string=query_string,
                                                 spelling_query=spelling_query, result_class=result_class)

        spelling_suggestion = self._spelling_suggestion(spelling_query, query_string)
        raise EmptyResults(spelling_suggestion=spelling_suggestion)

    def _process_results(self, raw_page, highlight=False, query_string='', spelling_query=None, result_class=None):
        results = []

        # It's important to grab the hits first before slicing. Otherwise, this
        # can cause pagination failures.
        hits = len(raw_page)

        if result_class is None:
            result_class = SearchResult

        facets = {}
        spelling_suggestion = None
        unified_index = connections[self.connection_alias].get_unified_index()
        indexed_models = unified_index.get_indexed_models()

        for doc_offset, raw_result in enumerate(raw_page):
            score = raw_page.score(doc_offset) or 0
            app_label, model_name = raw_result[DJANGO_CT].split('.')
            additional_fields = {}
            model = haystack_get_model(app_label, model_name)

            if model and model in indexed_models:
                for key, value in raw_result.items():
                    index = unified_index.get_index(model)
                    string_key = str(key)

                    if string_key in index.fields and hasattr(index.fields[string_key], 'convert'):
                        # Special-cased due to the nature of KEYWORD fields.
                        if index.fields[string_key].is_multivalued:
                            if value is None or len(value) is 0:
                                additional_fields[string_key] = []
                            else:
                                additional_fields[string_key] = value.split(',')
                        else:
                            additional_fields[string_key] = index.fields[string_key].convert(value)
                    else:
                        additional_fields[string_key] = self._to_python(value)

                del(additional_fields[DJANGO_CT])
                del(additional_fields[DJANGO_ID])

                if highlight:
                    sa = self.analyzer
                    formatter = WhooshHtmlFormatter('em')
                    terms = [token.text for token in sa(query_string)]

                    whoosh_result = whoosh_highlight(
                        additional_fields.get(self.content_field_name),
                        terms,
                        sa,
                        ContextFragmenter(),
                        formatter
                    )
                    additional_fields['highlighted'] = {
                        self.content_field_name: [whoosh_result],
                    }

                result = result_class(app_label, model_name, raw_result[DJANGO_ID], score, **additional_fields)
                results.append(result)
            else:
                hits -= 1

        if self.include_spelling:
            if spelling_query:
                spelling_suggestion = self.create_spelling_suggestion(spelling_query)
            else:
                spelling_suggestion = self.create_spelling_suggestion(query_string)

        return {
            'results': results,
            'hits': hits,
            'facets': facets,
            'spelling_suggestion': spelling_suggestion,
        }

    def _sort_by(self, sort_by):
        if sort_by is None:
            return

        sort_by_list = []
        for order_by in sort_by:
            if isinstance(order_by, six.string_types):
                if order_by.startswith('-'):
                    reverse = True
                    order_by = order_by[1:]
                else:
                    reverse = False
                if order_by == 'score':
                    if reverse:
                        warnings.warn("Whoosh does not handle reversed sorting by score.", Warning, stacklevel=2)
                    order_by = ScoreFacet()
                else:
                    order_by = FieldFacet(order_by, reverse=reverse)
            elif not isinstance(order_by, FacetType):
                warnings.warn("Whoosh does not handle sorting by %s." % repr(order_by), Warning, stacklevel=2)
            sort_by_list.append(order_by)

        sort_by = MultiFacet(sort_by_list) if len(sort_by_list) > 1 else sort_by_list[0]
        return sort_by

    def _narrow(self, narrow_queries, models, limit_to_registered_models):
        if limit_to_registered_models is None:
            limit_to_registered_models = getattr(settings, 'HAYSTACK_LIMIT_TO_REGISTERED_MODELS', True)

        if models and len(models):
            model_choices = sorted(get_model_ct(model) for model in models)
        elif limit_to_registered_models:
            # Using narrow queries, limit the results to only models handled
            # with the current routers.
            model_choices = self.build_models_list()
        else:
            model_choices = []

        if len(model_choices):
            if narrow_queries is None:
                narrow_queries = set()
            narrow_queries.add(' OR '.join('%s:%s' % (DJANGO_CT, rm) for rm in model_choices))

        if not narrow_queries:
            return

        narrowed_results = None

        # Potentially expensive? I don't see another way to do it in Whoosh...
        narrow_searcher = self.index.searcher()
        with closing(narrow_searcher):

            for nq in narrow_queries:
                recent_narrowed_results = narrow_searcher.search(self.parser.parse(force_text(nq)),
                                                                 limit=None)

                if len(recent_narrowed_results) <= 0:
                    raise EmptyResults

                if narrowed_results:
                    narrowed_results.filter(recent_narrowed_results)
                else:
                    narrowed_results = recent_narrowed_results

        return narrowed_results

    def _spelling_suggestion(self, spelling_query, query_string):
        if self.include_spelling:
            if spelling_query:
                spelling_suggestion = self.create_spelling_suggestion(spelling_query)
            else:
                spelling_suggestion = self.create_spelling_suggestion(query_string)
            return spelling_suggestion


class WhooshEngine(whoosh_backend.WhooshEngine):
    backend = WhooshSearchBackend
