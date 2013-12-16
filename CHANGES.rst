**************
Change History
**************

5.3.0 (2013-12-16)
==================

- Minor fix added ``spellcheckField`` to wrodbreak in spellchecker.
  [jod]
- Added ``extra-conf-files`` to schema generation. Now we can add extra files
  to conf folder.
  [jod]


5.2.1 (2013-10-22)
==================

- Fix formatting for change log and PyPI display
  [davidjb]


5.2 (2013-10-22)
================

- Ensure only one ``dataDir`` option is generated in ``solrconfig.xml``
  using the default template. Fixes start-up in Solr 4.5.0.
  [mitchellrj, pmcnr]

5.1 (2013-09-04)
================

- Ensure that changing part of a ``core`` section will cause Solr configuration
  to be regenerated. Fixes #24.
  [davidjb]
- ``logdir`` option is now available for ``logging.properties`` template.
  [pmcnr]
- Fix testing for Python 3 and enable Python 3.3 testing for Travis.
  [davidjb]
- Enable generation of ``log4j.properties`` from template (Solr >= 4.3 defaults
  to using log4j as its SLF4J implementation).
  [pmcnr]


5.0.1 (2013-06-24)
==================

- Minor reST changes to readme and change log to fix long description.
  [davidjb]


5.0 (2013-06-24)
================

- Recreate solr config on buildout update if the
  directory of the solr-instance was deleted.
  [mghh]

- New option 'additionalFieldConfig'.
  This option allows for additional configuration options
  in <fields>...</fields> section of schema.xml
  Use this if you have dynamicFields
  [mghh]

- New option 'directoryFactory'.
  Use it to define the solr directoryFactory for a Solr instance.
  [mghh]

- Allow Buildout to be re-run without breaking a running Solr instance.
  Previously, Solr required a restart to restore removed files.
  [Jc2k]

- Remove ``apache-`` prefix from artifact filenames (jar files) to handle
  naming changes introduced with Solr 4.1.  Versions earlier than 4.1 will
  see this prefix included within configuration files.
  [davidjb]

- Ensure Solr 4 templates do not have two ``autoCommit`` directives, mirroring
  how Solr 3 templates operate.

  **Backwards incompatibility**: if relying on a default ``autoCommit``
  directive in Solr 4, you must configure the ``autoCommitMaxDocs`` and/or
  ``autoCommitMaxTime`` recipe options.  A default is no longer provided.
  [davidjb]

- Python 3 support added. Python < 2.6 support dropped. Dropped
  dependency on iw.recipe.template as Cheetah does not support Python
  3. Replaced with Genshi, as used by collective.recipe.template.

  **Backwards incompatibility**: custom templates must be converted to
  Genshi format.
  [mitchellrj]

4.0.1 (unreleased)
==================

- Added additional-solrconfig-query allowing one to extend the solrconfig.xml
  query section.
  [naro]
- Add ability to specify location of pid file.
  [CheeseTheMonkey]


4.0 (2013-02-15)
================

- Add ability to control ``filter``, ``char-filter`` and ``tokenizer`` options
  for different analyzers (eg ``query`` and ``index`` analyzers). These
  options are named like ``filter-query``.
  [davidjb]
- Add ``tokenizer`` option for controlling the tokenizers set for default
  field type analyzers.
  [davidjb]
- Solr 4.0 support
  [silviot]
- Allow comments in index directive
  [silviot]
- Allow ``cores`` to be separated by newlines rather than just spaces.
  [domruf]
- Add ``char-filter`` as an option for setting CharFilterFactories for
  default field types.
  [davidjb]

3.8 (2012-08-09)
================

- Support ``default-core-name`` for specifying the name of a core to
  use for incoming Solr requests that do not specify a core. See
  http://wiki.apache.org/solr/CoreAdmin#cores
  [reinhardt]
- Add ability to add arbitrary configuration to ``schema.xml`` using
  ``additional-schema-config`` option.
  [davidjb]
- Add documentation and tests for ``copyfield`` option for indexes to test
  and clarify that this option is available.
  [davidjb]

3.7.1 (2012-02-28)
==================

- Fixed package missing files, without a MANIFEST.in we need setuptools-git.
  [jod]

3.7 (2012-02-28)
================

- Fixed tests.
  [jod]

- added option ``abortOnConfigurationError`` (makes config error diagnostics a lot
  easier).
  [gweis]

- Add support for field options ``termVectors``, ``termPositions`` and
  ``termOffsets``.
  [gweis]

- Use parts location to find additional jars.
  [gweis]

- Copy dist and contrib folder for Multicore setup (just like for Singlecore).
  [gweis]

- Diabled elevate.xml`, solar would fail to work if this is enabled.
  [gweis]

3.6 (2011-12-07)
================

- Account for new schema validation in Solr 3.4 related to ``omitNorms`` field.
  [hannosch]

- Update generated config files to match and require Solr 3.5.
  [hannosch]

- Fix ``solr-instance purge`` to work with hosts/ports other than localhost:8983
  [csenger]

- Added new ``extralibs`` option to include custom Java libraries

3.5 (2011-07-10)
================

- Removed the ``cacheSize`` option in favor of 8 specific options to configure
  every aspect of the query caches on their own.
  [hannosch]

- Added new ``spellcheckField`` option, to configure the source field for the
  spellcheck search component.
  [hannosch]

- Removed the example ``tvrh``, ``terms`` and ``elevate`` request handlers.
  [hannosch]

- Removed the example ``spell`` request handler and enabled spell checking based
  on the ``default`` field for the ``search`` request handler.
  [hannosch]

- Clean up solrconfig template and remove an example ``firstSearcher`` query.
  [hannosch]

- Added new ``mergeFactor``, ``ramBufferSizeMB``, ``unlockOnStartup`` options.
  [hannosch]

3.4 (2011-07-09)
================

- Update generated config files to match and require Solr 3.3.
  [hannosch]

- Add ``solr.WordDelimiterFilterFactory`` to the standard text field, to split on
  intra-word delimiters such as ``-_:``.
  [hannosch]

3.3 (2011-06-25)
================

- Increase the ``requestParsers-multipartUploadLimitInKB`` default value from
  2mb to 100mb to allow the ``update/extract`` handler to accept large files.
  [hannosch]

- Increase Jetty's ``maxFormContentSize`` from 1mb to 100mb to allow indexing
  large files.
  [hannosch]

- Changed the field definition of the ``text`` type to avoid filters specific to
  the English language and instead use a default filter config that should work
  with most languages, based on the ICU tokenizer and folding filter.
  [hannosch]

- Load the ``analysis-extras`` libraries, so we can use the `ICU`-based filters
  and tokenizers.
  [hannosch]

- Removed the clustering request handlers from the default config, as they
  didn't work anyways without us loading the ``contrib/clustering`` libraries.
  [hannosch]

- Enable ``Tika`` data extraction and Solr Cell libraries. Data is extracted into
  a field called ``tika_content`` unless specified otherwise in each request via
  the ``fmap.content=`` argument. All extracted fields which aren't in the schema
  are put into dynamic fields prefixed with ``tika_``.
  [tom_gross, hannosch]

- Removed the Velocity driven ``/browse`` request handler. The example config
  we generated didn't match the schema.
  [hannosch]

3.2 (2011-06-23)
================

- Added a new option ``stopwords-template`` which allows you to specify a custom
  stopwords file.
  [hannosch]

3.1 (2011-06-06)
================

- Updated templates to match default found in Solr 3.2.
  [hannosch]

3.0 (2011-06-04)
================

- We no longer require elementtree.
  [hannosch]

- Use the standard libraries doctest module.
  [hannosch]

- Increase the ``max-num-results`` default value from 10 to 500 to avoid
  restricting search results on this low level. The application layer should
  be responsible for making such restrictions.
  [hannosch]

3.0a2 (2011-05-26)
==================

- Added new ``logging-template`` option and instruct Jetty to use the
  ``logging.properties`` file. The default logging level is set to ``WARNING``.
  [hannosch]

- Pass the ``host`` option to the Jetty config, so it can be configured to listen
  only on localhost or a specific IP.
  [hannosch]

- Disabled Jetty request log.
  [hannosch]

- Updated ``jetty.xml`` template to match new defaults found in the Solr 3.1
  release.
  [hannosch]

- Fixed syntax error introduced around ``httpCaching`` directive.
  [hannosch]

3.0a1 (2011-05-26)
==================

- Updated the solrconfig.xml template to match the template from Solr 3.1.
  [hannosch]

- Updated the default ``schema.xml`` to the Solr 3.1 format. The schema version
  is now ``1.3`` instead of ``1.2``. The schema is no longer compatible with
  Solr 1.4. Please use a recipe version from the 2.x series for that.

  Changes to the schema include:

  * Fields no longer have a compressed option.

  * The default schema defines three new field types: ``point``, ``location`` and
    ``geohash`` useful for geospatial data.

  If you have an older Solr 1.4 index, you should be able to continue using it
  without a full reindex.
  [hannosch]

2.1 (2011-04-12)
================

- Fixed reStructuredText.
  [jod]

2.0 (2011-04-12)
================

- Added ``default`` to filter attributes.
  [jod]

- Multicore recipe ``collective.recipe.solrinstance:mc``. [jod]

  * Refactured to get multicore working.

  * Pinned buildout version to get tests working.

1.1 (2011-04-04)
================

- Make jetty.xml.tmpl honor the host parameter.
  [davidblewett]

- Support for Windows
  [bluszcz]

1.0 (2010-12-12)
================

- No changes.

1.0b5 (2010-09-03)
==================

- Actually provide the default value for the ``cacheSize`` option.
  [hannosch]

1.0b4 (2010-08-12)
==================

- Added ``jetty-template`` option.
  [ajung]

1.0b3 (2010-07-23)
==================

- Don't kill solr after script finish when script is just used for starting
  solr as a daemon
  [do3cc]

1.0b2 (2010-06-01)
==================

- Actually do something in the update call. Now the configuration is updated
  when you run buildout again.
  [fschulze]

- Handle termination signal in the wrapper script, so the solr instance is
  killed when the wrapper dies.
  [fschulze]

1.0b1 (2010-05-25)
==================

- Added new ``autoCommitMaxDocs`` and ``autoCommitMaxTime`` options.
  [hannnosch]

- ``logdir`` option internal bugfix: buildout does not allow ``None`` options
  values (__setitem__).
  [anguenot]

1.0a7 (2010-05-17)
==================

- Fixed syntax error in new logdir code.
  [ajung]

1.0a6 (2010-05-17)
==================

- Added ``logdir`` option.
  [ajung]

1.0a5 (2010-05-11)
==================

- Added more options: ``maxWarmingSearchers``, ``useColdSearcher`` and
  ``cacheSize``.
  [hannosch]

1.0a4 (2010-05-05)
==================

- Added back JMX configuration. See http://wiki.apache.org/solr/SolrJmx for
  more details. You can enable it by adding ``-Dcom.sun.management.jmxremote``
  to the ``java_opts`` option.
  [hannosch]

1.0a3 (2010-03-23)
==================

- Added back a field type called ``integer`` with the same properties as the
  ``int`` type. This ensures basic schemas created by ``collective.solr`` won't
  need any schema changes, though they still need a full reindex.
  [hannosch]

1.0a2 (2010-03-22)
==================

- Fixed invalid reStructuredText format in the changelog.
  [hannosch]

1.0a1 (2010-03-22)
==================

- Replaced the ``gettableFiles`` option in the admin section with the new
  ``*.admin.ShowFileRequestHandler`` approach. By default your entire
  ``SOLR_HOME/conf`` except for the ``scripts.conf`` is exposed.
  [hannosch]

- Updated the default ``schema.xml`` to the Solr 1.4 format. The schema version
  is now ``1.2`` instead of ``1.1``. The schema is no longer compatible with
  Solr 1.3. Please use a recipe version from the 0.x series for that.

  Changes to the schema include:

  * The integer field is now called int.

  * New field type attribute ``omitTermFreqAndPositions`` introduced. This is
    true by default except for text fields.

  * New binary and random field types.

  * The int, float, long, double and date fields now use the ``solr.Trie*``
    classes. These are more efficient in general.

  * New tint, tfloat, tlong, tdouble and tdate fields. These are ``solr.Trie*``
    fields with a precisionStep configured. You can use them for fields that
    see a lot of range queries.

  * The old sint, slong, sfloat and sdouble fields are no longer configured.

  * The examples fields text_greek, textTight and alphaOnlySort are no longer
    configured by default.

  * The text field uses the SnowballPorterFilterFactory with a language of
    English instead of the EnglishPorterFilterFactory.

  * The ignored field is now multiValued.

  * No dynamic fields are configured by default.

  If you have an older Solr 1.3 configuration, you might need to adjust it to
  match some of the new defaults. You will also have to do a full reindex of
  Solr, if the type of any of the fields changed, like with int or date fields.
  [hannosch]

- Simplify solrconfig.xml and unconfigure example handlers that rely on a
  specific schema. Other changes include:

  * Indexes are now flushed when the ramBufferSizeMB is exceeded, defaulting to
    32mb instead of every 1000 documents. The maxBufferedDocs is deprecated.

  * The new reopenReaders option causes IndexReaders to be reopened instead of
    closed and then opened.

  * The filterCache uses the solr.FastLRUCache instead of the solr.LRUCache.

  * The queryResultWindowSize defaults to 30 instead of 10.

  * The requestHandler use the new solr.SearchHandler, which supports a
    defType argument to turn it into a dismax handler, instead of having two
    separate classes for the two handlers.

  There is a number of new handlers in Solr 1.4, which aren't enabled by
  default. Read the Solr documentation for the examples.
  [hannosch]

- Updated jetty.xml and solrconfig.xml to Solr 1.4 defaults. The
  ``*.jetty.Request.maxFormContentSize`` has been set to allow post request of
  1mb by default.
  [hannosch]

- Made the tests pass again, by installing more packages into the test buildout
  environment.
  [hannosch]

0.4 (2010-02-18)
================

- Some package metadata cleanup.
  [hannosch]

- Added optional java_opts parameter to pass to the Java Virtual
  Machine (JVM) used to run Solr.
  [anguenot]

- Fixed to create the ``solr.log`` file inside the ``log`` folder.
  [deo]

- Made sure to display the invalid index attribute name when raising
  the related error.
  [deo]

- Added support for defining custom field types.
  [deo]

- Added a ``restart`` command to the solr instance control script.
  [deo]


0.3 (2009-09-10)
================

- Added requestParsers-multipartUploadLimitInKB allowing one to
  adjust the request parsers limit.
  [anguenot]

- Added additional-solrconfig allowing one to extend the solrconfig.xml.
  [anguenot]

- Support whitespace in schema index attributes values.
  [anguenot]

- Added default-operator.
  [swampmonkey]

- Added config-template for allowing an alternate template to be used for
  generating the solrconfig.xml file.
  [cguardia]

- Added the ``vardir`` and ``script`` options, making it possible to
  install multiple Solr instances in a single buildout.
  [hathawsh]


0.2 (2008-08-08)
================

- Improved stop command by using SIGTERM instead of SIGHUP.
  [guido_w]

- Made that stdout and stderr get redirected to a log file when daemonizing
  the solr instance.
  [guido_w]

- Added support for setting Solr filters.
  [deo]


0.1 (2008-07-07)
================

- First public release.
  [dokai]
