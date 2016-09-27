# coding: utf-8

from __future__ import absolute_import

from haystack import indexes


class FuzzySearchIndexMixin(indexes.SearchIndex):
    text_fuzzy = indexes.EdgeNgramField()

    def prepare(self, obj):
        prepared_data = super(FuzzySearchIndexMixin, self).prepare(obj)
        content = prepared_data[self.get_content_field()]
        prepared_data['text_fuzzy'] = content
        return prepared_data


class FuzzySearchIndex(FuzzySearchIndexMixin,
                       indexes.BasicSearchIndex):
    pass


class ModelFuzzySearchIndex(FuzzySearchIndexMixin,
                            indexes.ModelSearchIndex):
    pass
