# coding: utf-8

from __future__ import absolute_import

from haystack.signals import BaseSignalProcessor
from nhaystack.signals import ModelSignalProcessorMixin


class RealtimeModelSignalProcessor(ModelSignalProcessorMixin,
                                   BaseSignalProcessor):
    INDEXED_MODELS = ('music.musician', 'music.album')

    SENDER_MAP = {
        'music.musician': ('albums',),
        'music.album': ('artist',),
    }
