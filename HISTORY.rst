.. :changelog:

History
-------

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
