.. :changelog:

History
-------

0.0.5 (2016-12-23)
++++++++++++++++++
* [core] Fixed unhandled exception on updating index for an related object that
  has already been deleted (within a transaction).

0.0.4 (2016-10-19)
++++++++++++++++++
* [core] Fixed elif/if bug for a case when the same model should be registered in both
  INDEXED_MODELS and SENDER_MAP for a signal processor.

0.0.3 (2016-10-14)
++++++++++++++++++
* [core] Added signals.ModelSignalProcessorMixin.teardown() to be able to
  disconnect signal handlers of the.signal processor instance that have
  been connected by .setup() during the Haystack initialization.
* [utils] Added HaystackTestSuiteRunnerMixin to support protection of main
  search index from been altered during unit test runs.
* [tests] Added simple test case for checking signal handlers disconnection
  on signal processor teardown.

0.0.2 (2016-10-12)
++++++++++++++++++
* [core] Fixed signals.ModelSignalProcessorMixin to properly register signal
  handlers.
* [tests] Added an initial Django test project settings and a testing
  application for further tests.
* Updated tox and Travis-CI settings.

0.0.1 (2016-09-27)
++++++++++++++++++

* Initial release
* [ES] Added support for ELASTICSEARCH_FIELD_MAPPINGS and 'FIELD_MAPPINGS'
  Haystack connection setting.
* [ES] Fixed '_boost' to be used with Elastic < 2.0.0 back again.
* [ES] Do not store 'id' attribute in the Elastic index together with '_id'
  (index size optimization).
* [ES] Added explicit support for Elastic 'boolean' type and 'null' value
  when building a query.
* [ES] Added 'migrate_index' command to handle server-side index rebuild on
  Elastic server; useful when only Elastic mapping has changed in the code.
  Inspired by `this blog article <http://cstrap.blogspot.ru/2015/06/dealing-with-elasticsearch-reindex-and.html>`_
