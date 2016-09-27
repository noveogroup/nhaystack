# coding: utf-8

from __future__ import absolute_import

from functools import partial

from django.db.models import signals as models_signals
from django.utils.itercompat import is_iterable

from haystack.utils import get_model_ct


class ModelSignalProcessorMixin(object):
    """
    Allows for observing when saves/deletes fire & automatically updates the
    search engine appropriately.

    INDEXED_MODELS = ('auth.User',)

    SENDER_MAP = {
        'auth.Group': ('user_set',),
    }
    """
    handle_action_prefix = 'handle'

    def setup(self):
        models_signals.class_prepared.connect(self._post_setup)

    def _post_setup(self, sender, **kwargs):
        model_name = get_model_ct(sender)

        _handle_save = self._get_action_handler('save')
        _handle_delete = self._get_action_handler('delete')

        if model_name in self.INDEXED_MODELS:
            models_signals.post_save.connect(_handle_save, sender=sender)
            models_signals.post_delete.connect(_handle_delete, sender=sender)
        elif model_name in self.SENDER_MAP:
            models_signals.post_save.connect(
                partial(self._handle_related_action, _handle_save),
                sender=sender
                )
            models_signals.post_delete.connect(
                partial(self._handle_related_action, _handle_delete),
                sender=sender
            )

    def _get_action_handler(self, action):
        action_handler = getattr(
            self, '{}_{}'.format(self.handle_action_prefix, action)
        )
        return action_handler

    def _get_related_instance(self, instance, field_name):
        rel_instance = getattr(instance, field_name, None)
        try:
            # check if field is m2m
            rel_instance = rel_instance.all()
        except AttributeError:
            if callable(rel_instance):
                rel_instance = rel_instance(instance)

        return rel_instance

    def _handle_related_action(self, action_handler, sender, instance, **kwargs):
        model_name = sender.__name__

        for field_name in self.SENDER_MAP[model_name]:
            rel_instance = self._get_related_instance(instance, field_name)

            if is_iterable(rel_instance):
                for r in rel_instance:
                    action_handler(r.__class__, r, **kwargs)
            else:
                action_handler(rel_instance.__class__, rel_instance, **kwargs)
