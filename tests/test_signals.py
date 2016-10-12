# coding: utf-8

from __future__ import absolute_import

from django.db.models import signals


def test_signal_handlers_registered():
    assert len(signals.post_save.receivers) > 0
    assert len(signals.post_delete.receivers) > 0
