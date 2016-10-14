# coding: utf-8

from __future__ import absolute_import

from django.test.utils import override_settings

import haystack
from haystack.utils import loading


class HaystackTestSuiteRunnerMixin(object):
    base_signal_processor_path = 'haystack.signals.BaseSignalProcessor'
    test_settings = {}

    def patch_connections(self):
        haystack.connections = loading.ConnectionHandler({
            haystack.DEFAULT_ALIAS: {
                'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
            },
        })

    def patch_signal_processor(self):
        if haystack.signal_processor_path != self.base_signal_processor_path:
            haystack.signal_processor.teardown()
            haystack.signal_processor_path = self.base_signal_processor_path
            haystack.signal_processor_class = loading.import_class(
                haystack.signal_processor_path
            )
            haystack.signal_processor = haystack.signal_processor_class(
                haystack.connections, haystack.connection_router
            )

    def run_tests(self, *args, **kwargs):
        self.patch_connections()
        self.patch_signal_processor()
        with override_settings(
            HAYSTACK_SIGNAL_PROCESSOR=self.base_signal_processor_path,
            **self.test_settings
        ):
            return super(HaystackTestSuiteRunnerMixin, self).run_tests(*args, **kwargs)
