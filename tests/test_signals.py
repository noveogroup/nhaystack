# coding: utf-8

from __future__ import absolute_import

from django.db.models import signals

import haystack


def test_signal_handlers_registered():
    assert len(signals.post_save.receivers) > 0
    assert len(signals.post_delete.receivers) > 0

def test_signal_handlers_cleaned_on_teardown():
    original_class_prepared_handlers_length = len(signals.class_prepared.receivers)
    haystack.signal_processor.teardown()
    assert len(signals.post_save.receivers) == 0
    assert len(signals.post_delete.receivers) == 0
    expected = original_class_prepared_handlers_length - 1
    assert len(signals.class_prepared.receivers) == expected
    haystack.signal_processor.setup()
