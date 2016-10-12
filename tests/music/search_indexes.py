# coding: utf-8

from __future__ import absolute_import

from haystack import indexes
from haystack.utils.app_loading import haystack_get_models


def get_model(app_and_model):
    return haystack_get_models(app_and_model)[0]


class MusicianSearchIndex(indexes.ModelSearchIndex, indexes.Indexable):

    def get_model(self):
        return get_model('music.Musician')


class AlbumSearchIndex(indexes.ModelSearchIndex, indexes.Indexable):

    def get_model(self):
        return get_model('music.Album')
