# coding: utf-8

from __future__ import absolute_import

from functools import partial
from inspect import ismethod

from django.db.models import signals as models_signals
from django.utils import six

from haystack.utils import get_model_ct

METHOD_SELF = '__self__' if six.PY3 else 'im_self'


class ModelSignalProcessorMixin(object):
    """
    Allows for observing when saves/deletes fire & automatically updates the
    search engine appropriately.

    INDEXED_MODELS = ('auth.user',)

    SENDER_MAP = {
        'auth.group': ('user_set',),
    }
    """
    handle_action_prefix = 'handle'

    def setup(self):
        def get_action_handler(action):
            action_handler = getattr(
                self, '{}_{}'.format(self.handle_action_prefix, action)
            )
            return action_handler

        _handle_save = get_action_handler('save')
        _handle_delete = get_action_handler('delete')
        self.__dict__.update({
            '_handle_save': _handle_save,
            '_handle_delete': _handle_delete,
            '_handle_related_save': partial(self._handle_related_action, _handle_save),
            '_handle_related_delete': partial(self._handle_related_action, _handle_delete),
        })
        models_signals.class_prepared.connect(self._post_setup)

    def teardown(self):
        models_signals.class_prepared.disconnect(self._post_setup)
        signals = (models_signals.post_save, models_signals.post_delete)

        def is_method_of_self(receiver):
            handler = receiver[1]()
            return (ismethod(handler) and
                    getattr(handler, METHOD_SELF, None) != self)

        for signal in signals:
            with signal.lock:
                signal.receivers = [receiver for receiver in signal.receivers
                                    if is_method_of_self(receiver)]
                signal.sender_receivers_cache.clear()

    def _post_setup(self, sender, **kwargs):
        model_name = get_model_ct(sender)
        if model_name in self.INDEXED_MODELS:
            models_signals.post_save.connect(self._handle_save, sender=sender)
            models_signals.post_delete.connect(self._handle_delete, sender=sender)
        elif model_name in self.SENDER_MAP:
            models_signals.post_save.connect(self._handle_related_save, sender=sender)
            models_signals.post_delete.connect(self._handle_related_delete, sender=sender)

    def _handle_related_action(self, action_handler, sender, instance, **kwargs):
        model_name = get_model_ct(sender)
        for field_name in self.SENDER_MAP[model_name]:
            rel_instances = self._get_related_instances(instance, field_name)
            for rel_instance in rel_instances:
                action_handler(rel_instance.__class__, rel_instance, **kwargs)

    def _get_related_instances(self, instance, field_name):
        rel_instance = getattr(instance, field_name, None)
        if callable(rel_instance):
            rel_instance = rel_instance(instance)
        try:
            # check if field is m2m
            rel_instances = rel_instance.all()
        except AttributeError:
            rel_instances = (rel_instance,)
        return rel_instances
