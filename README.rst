**************************************
Recipe for configuring a Solr instance
**************************************

.. contents::

The recipe configures an instance of the Solr_ indexing server. Solr
is an open source enterprise search server based on the Lucene_ Java
search library, with XML/HTTP and JSON APIs, hit highlighting, faceted
search, caching, replication, and a web administration interface

Git Repository and issue tracker:
https://github.com/collective/collective.recipe.solrinstance

.. |travisci| image::  https://travis-ci.org/collective/collective.recipe.solrinstance.png
.. _travisci: https://travis-ci.org/collective/collective.recipe.solrinstance

|travisci|_

.. _Solr : http://lucene.apache.org/solr/
.. _Lucene : http://lucene.apache.org/java/docs/index.html


Notes
=====

- This version of the recipe supports Solr 3.5, 4.x (including 4.0, 4.1, 4.2
  and 4.5). Please use a release from the 2.x series if you are using Solr 1.4.

- This version supports Genshi_ templates **only**. Please use a release
  less than 5.x if you require Cheetah_ templating and do not require
  Python 3 support. If you require Python 3 support, you must convert
  any custom templates to use the `Genshi text templating language`_.

.. _Genshi : http://genshi.edgewall.org/
.. _Cheetah: http://www.cheetahtemplate.org/
.. _`Genshi text templating language` : http://genshi.edgewall.org/wiki/Documentation/text-templates.html

Supported options
*****************

The recipe supports the following options.

Solr Server
===========

solr-location
    Path to the location of the Solr installation. This should be
    the top-level installation directory.

host
    Name or IP address of the Solr server, e.g. some.server.com.
    Defaults to ``localhost``.

port
    Server port. Defaults to ``8983``.

basepath
    Base path to the Solr service on the server. The final URL to the
    Solr service will be made of::

       $host:$port/$basepath

    to which the actual commands will be appended. Defaults to ``/solr``.

vardir
    Optional override for the location of the directory where Solr
    stores its indexes and log files. Defaults to
    ``${buildout:directory}/var/solr``. This option and the ``script``
    option make it possible to create multiple Solr instances in a
    single buildout and dedicate one or more of the instances to
    automated functional testing.

logdir
    Optional override for the location of the Solr logfiles.
    Defaults to ``${buildout:directory}/var/solr``.

pidpath
    Optional override for the location of the Solr pid file.
    Defaults to ``${buildout:directory}/var/solr``.

jetty-template
    Optional override for the ``jetty.xml`` template. Defaults to
    ``templates/jetty.xml.tmpl``.

log4j-template
    Optional override for the ``log4j.properties`` template. Defaults to
    ``templates/log4j.properties.tmpl``.

logging-template
    Optional override for the ``logging.properties`` template. Defaults to
    ``templates/logging.properties.tmpl``.

jetty-destination
    Optional override for the directory where the ``jetty.xml`` file
    will be generated. Defaults to the Solr default location.

extralibs
    Optional includes of custom Java libraries. The option takes
    a path and a regular expression per line separated by a colon.
    The regular expression is optional and defaults to ``.*\.jar``
    (all jar-files in a directory). Example::

        extralibs =
            /my/global/java/path
            some/special/libs:.*\.jarx

script
    Optional override for the name of the generated Solr instance
    control script. Defaults to ``solr-instance``. This option and the
    ``vardir`` option make it possible to create multiple Solr
    instances in a single buildout and dedicate one or more of the
    instances to automated functional testing.

java_opts
    Optional. Parameters to pass to the Java Virtual Machine (JVM) used to
    run Solr. Each option is specified on a separated line.
    For example::

        [solr-instance]
        ...
        java_opts =
          -Xms512M
          -Xmx1024M
        ...

Solr Configuration
==================

config-destination
    Optional override for the directory where the ``solrconfig.xml``
    file will be generated. Defaults to the Solr default location.

config-template
    Optional override for the template used to generate the ``solrconfig.xml``
    file. Defaults to the template contained in the recipe, i.e.
    ``templates/solrconfig.xml.tmpl``.

max-num-results
    The maximum number of results the Solr server returns. This sets the
    ``rows`` option for the request handlers. Defaults to 500.

maxWarmingSearchers
    Maximum number of searchers that may be warming in the background.
    Defaults to ``4``. For read-only slaves recommend to set to ``1`` or ``2``.

useColdSearcher
    If a request comes in without a warm searcher available, immediately use
    one of the warming searchers to handle the request. Defaults to ``false``.

mergeFactor
    Specify the index defaults merge factor. This value determines how many
    segments of equal size exist before being merged to a larger segment. With
    the default of ``10``, nine segments of 1000 documents will be created before
    they are merged into one containing 10000 documents, which in turn will be
    merged into one containing 100000 documents once that size is reached.

ramBufferSizeMB
    Sets the amount of RAM that may be used by Lucene indexing for buffering
    added documents and deletions before they are flushed to the directory.
    Defaults to 16mb.

unlockOnStartup
    If ``true`` (the recipes default), unlock any held write or commit locks on
    startup. This defeats the locking mechanism that allows multiple processes to
    safely access a Lucene index.

abortOnConfigurationError
    If set to ``true``, the Solr instance will not start up if there are
    configuration errors. This is useful in development environments to debug
    potential issues with schema and solrconfig. Defaults to ``false``.

spellcheckField
    Configures the field used as a source for the spellcheck search component.
    Defaults to ``default``.

autoCommitMaxDocs
    Lets you enable auto commit handling and force a commit after at least
    the number of documents were added. This is disabled by default.

autoCommitMaxTime
    Lets you enable auto commit handling after a specified time in
    milliseconds. This is disabled by default.

updateLog
    if updateLog is enabled an additional field ``_version_`` will be added
    to schema and updateLog will be enabled in updateHandler. This is required
    if you want to use Atomic Updates in Solr > 4.0. See:
    https://wiki.apache.org/solr/Atomic_Updates, defaults to ``false``.

requestParsers-enableRemoteStreaming
    Let's you enable remote streaming. Defalts to ``false`` as this is the Solr
    default.

requestParsers-multipartUploadLimitInKB
    Optional ``<requestParsers />`` parameter useful if you are submitting
    very large documents to Solr. May be the case if Solr is indexing binaries
    extracted from request.

directoryFactory
    Solr4 allows for different directoryFactories:
    solr.StandardDirectoryFactory, solr.MMapDirectoryFactory,
    solr.NIOFSDirectoryFactory, solr.SimpleFSDirectoryFactory,
    solr.RAMDirectoryFactory or solr.NRTCachingDirectoryFactory.
    The default is: solr.NRTCachingDirectoryFactory
    If you are running a solr-instance for unit-testing of an
    application it could be useful to use solr.RAMDirectoryFactory.

additional-solrconfig
    Optional additional configuration to be included inside the
    ``solrconfig.xml``. For instance, ``<requestHandler />`` directives.

additional-solrconfig-query
    Optional additional configuration to be included inside the
    query section of ``solrconfig.xml``.
    For instance, ``<listener />`` directives.


Cache Options
=============

Fine grained control of query caching as described at
http://wiki.apache.org/solr/SolrCaching.

The supported options are:

- ``filterCacheSize``
- ``filterCacheInitialSize``
- ``filterCacheAutowarmCount``
- ``queryResultCacheSize``
- ``queryResultCacheInitialSize``
- ``queryResultCacheAutowarmCount``
- ``documentCacheSize``
- ``documentCacheInitialSize``
- ``documentCacheAutowarmCount`` (only for Solr 4)


Schema
======

schema-destination
    Optional override for the directory where the ``schema.xml`` file
    will be generated. Defaults to the Solr default location.

schema-template
    Optional override for the template used to generate the ``schema.xml``
    file. Defaults to the template contained in the recipe, i.e.
    ``templates/schema.xml.tmpl``.

stopwords-template
    Optional override for the template used to generate the ``stopwords.txt``
    file. Defaults to the template contained in the recipe, i.e.
    ``templates/stopwords.txt.tmpl``.

extra-field-types
    Configure the extra field types available to be used in the
    ``index`` option. You can create custom field types with special
    analyzers and tokenizers, check Solr's complete reference:
    http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters

extra-conf-files
    Add extra files to conf folder like synonyms.txt or hunspell files
    https://wiki.apache.org/solr/Hunspell

filter
    Configure filters for analyzers for the default field types.
    These accept tokens produced by a given ``tokenizer`` and process them
    in series to either add, change or remove tokens. After all filters
    have been applied, the resulting token stream is indexed into the given
    field.

    This option applies to the default analyzer for a given field -- by
    default, Solr considers this to apply to both ``query`` and ``index``
    analyzers.  If you want to configure separate analyzers, see the
    ``filter-query`` and ``filter-index`` options below.

    Each filter is configured on a separated line and each filter will be
    applied to tokens (during Solr operation) in the order specified.

    Each line should read like::

        text solr.EdgeNGramFilterFactory minGramSize="2" maxGramSize="15" side="front"

    In the above example:

    * ``text`` is the ``type``, one of the built-in field types;
    * ``solr.EdgeNGramFilterFactory`` is the ``class`` for this filter; and
    * ``minGramSize="2"  maxGramSize="15" side="front"`` are the parameters
      for the filter's configuration. They should be formatted as XML
      attributes.

    By default, for the default analyzer (being both ``query`` and ``index``):

    * ``text`` fields are filtered using:

      * ``solr.ICUFoldingFilterFactory``
      * ``solr.WordDelimiterFilterFactory``
      * ``solr.TrimFilterFactory``
      * ``solr.StopFilterFactory``

    To suppress default behaviour, configure the ``filter`` option accordingly.
    If you want no filters, then set ``filter =`` (as an empty option) in your
    Buildout configuration. This is useful in the situation where you want no
    default filters and want full control over specifying filters on a
    per-analyzer basis.

    Check the available filters in Solr's documentation:
    http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters#TokenFilterFactories

filter-query
    Configure filters for default field types for ``query`` analyzers only.
    This option is like ``filter`` but only applies to the ``query`` analyzer
    for a given field.

    Configuration syntax is the same as the ``filter`` option above.  Options
    specified here will be added after any that apply from usage of the main
    ``filter`` option.

filter-index
    Configure filters for default field types for ``index`` analyzers only.
    This option is like ``filter`` but only applies to the ``index`` analyzer
    for a given field.

    Configuration syntax is the same as the ``filter`` option above.  Options
    specified here will be added after any that apply from usage of the main
    ``filter`` option.

char-filter
    Configure character filters (``CharFilterFactories``) for analyzers for the
    default field types. These are pre-processors for input characters
    in Solr fields or queries (consuming and producing a character stream) that
    can add, change or remove characters while preserving character position
    information

    This option applies to the default analyzer for a given field -- by
    default, Solr considers this to apply to both ``query`` and ``index``
    analyzers.  If you want to configure separate analyzers, see the
    ``char-filter-query`` and ``char-filter-index`` options below.

    Each char filter is configured on a separated line, following the same
    configuration syntax as the ``filter`` option above.  Each char filter will
    be applied to tokens (during Solr operation) in the order specified.

    By default, no char filters are specified for any analyzers.

    Information about available character filters is available in
    Solr's documentation: http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters#CharFilterFactories

char-filter-query
    Configure character filters for default field types for ``query`` analyzers
    only.  This option is like ``char-filter`` but only applies to the
    ``query`` analyzer for a given field type.

    Configuration syntax is the same as the ``filter`` option above.  Options
    specified here will be added after any that apply from usage of the main
    ``char filter`` option.

char-filter-index
    Configure character filters for default field types for ``index`` analyzers
    only.  This option is like ``char-filter`` but only applies to the
    ``index`` analyzer for a given field type.

    Configuration syntax is the same as the ``filter`` option above.  Options
    specified here will be added after any that apply from usage of the main
    ``char filter`` option.

tokenizer
    Configure tokenizers for analyzers for the default field types.

    This option applies to the default analyzer for a given field -- by
    default, Solr considers this to apply to both ``query`` and ``index``
    analyzers.  If you want to configure separate analyzers, see the
    ``tokenizer-query`` and ``tokenizer-index`` options below.

    Each tokenizer is configured on a separated line, following the same
    configuration syntax as the ``filter`` option above. Only one tokenizer
    may be specified per analyzer type for a given field type.  If you specify
    multiple tokenizers for the same field type, the last one specified will
    take precedence.

    By default, for the default analyzer (being both ``query`` and ``index``):

     * ``text`` fields are tokenized using ``solr.ICUTokenizerFactory``
     * ``text_ws`` fields are tokenized using
       ``solr.WhitespaceTokenizerFactory``

tokenizer-query
    Configure a tokenizer for default field types for ``query`` analyzers
    only.  This option is like ``tokenizer``, but only applies to the
    ``query`` analyzer for a given field type.

    Configuration syntax is the same as the ``filter`` option above.
    Options specified here will overide any that apply from usage of the main
    ``tokenizer`` option. For instance, if you specified a ``text_ws``
    tokenizer within the ``tokenizer`` option, and re-specify another
    ``text_ws`` tokenizer here, then this will take precedence.  Other field
    types will not be affected if not overriden.

tokenizer-index
    Configure a tokenizer for default field types for ``index`` analyzers
    only.  This option is like ``tokenizer``, but only applies to the
    ``index`` analyzer for a given field type.

    Configuration syntax is the same as the ``filter`` option above.
    Options specified here will overide any that apply from usage of the main
    ``tokenizer`` option. For instance, if you specified a ``text_ws``
    tokenizer within the ``tokenizer`` option, and re-specify another
    ``text_ws`` tokenizer here, then this will take precedence.  Other field
    types will not be affected if not overriden.

index
    Configures the different types of index fields provided by the
    Solr instance. Each field is configured on a separated line. Each
    line contains a white-space separated list of ``[key]:[value]``
    pairs which define options associated with the index. Common
    field options are detailed at
    http://wiki.apache.org/solr/SchemaXml#Common_field_options and
    are illustrated in following examples.

    A special ``[key]:[value]`` pair is supported here for supporting `Copy
    Fields`; if you specify ``copyfield:dest_field``, then a ``<copyField>``
    declaration will be included in the schema that copies the given field into
    that of ``dest_field``.

unique-key
    Optional override for declaring a field to be unique for all documents.
    See http://wiki.apache.org/solr/SchemaXml for more information
    Defaults to 'uid'.

default-search-field
    Configure a default search field, which is used when no field was
    explicitly given. See http://wiki.apache.org/solr/SchemaXml.

default-operator
    The default operator to use for queries.  Valid values are ``AND``
    and ``OR``. Defaults to ``OR``.

additional-schema-config
    Optional additional configuration to be included inside the
    ``schema.xml``. For instance, custom ``<copyField />`` directives
    and anything else that's part of the schema configuration (see
    http://wiki.apache.org/solr/SchemaXml).

additionalFieldConfig
    Optional additional configuration which is placed inside the
    ``<fields>...</fields>`` directive in ``schema.xml``. Use this to insert
    dynamic fields. For example::

        additionalFieldConfig =
            <dynamicField name="..." type="string" indexed="true" stored="true" />

    Defaults to ``''`` (empty string).

Multi-core
==========

The following options only apply if ``collective.recipe.solrinstance:mc`` is
specified. They are optional if the normal recipe is being used.
All options defined in the solr-instance section will we inherited to cores.
A core could override a previous defined option.

cores
    A list of identifiers of Buildout configuration sections that correspond
    to individual Solr core configurations. Each identifier specified will
    have the section it relates to processed according to the given options
    above to generate Solr configuration files for each core.  See `Multi-core
    Solr`_ for an example.

    Each identifier specified will result in a Solr ``instanceDir`` being
    created and entries for each core placed in Solr's ``solr.xml``
    configuration.

default-core-name
    Optional. This option controls which core is set as the default for
    incoming requests that do not specify a core name. This corresponds to
    the ``defaultCoreName`` option described at
    http://wiki.apache.org/solr/CoreAdmin#cores.

Zope Integration
================

section-name
    Name of the ``product-config`` section to be generated for ``zope.conf``.
    Defaults to ``solr``.

zope-conf
    Optional override for the configuration snippet that is generated to
    be included in ``zope.conf`` by other recipes. Defaults to::

        <product-config ${part:section-name}>
            address ${part:host}:${part:port}
            basepath ${part:basepath}
        </product-config>

Examples
********


Single Solr
===========

A simple example how a single Solr configuration could look like this::

    [buildout]
    parts = solr-download
            solr

    [solr-download]
    recipe = hexagonit.recipe.download
    strip-top-level-dir = true
    url = http://mirrorservice.nomedia.no/apache.org//lucene/solr/3.5.0/apache-solr-3.5.0.zip

    [solr]
    recipe = collective.recipe.solrinstance
    solr-location = ${solr-download:location}
    host = 127.0.0.1
    port = 1234
    max-num-results = 500
    section-name = SOLR
    unique-key = uniqueID
    index =
        name:uniqueID type:string indexed:true stored:true required:true
        name:Foo type:text copyfield:Baz
        name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true copyfield:Baz
        name:Foo bar type:text
        name:Baz type:text
        name:Everything type:text
    filter =
        text solr.LowerCaseFilterFactory
    char-filter-index =
        text solr.HTMLStripCharFilterFactory
    tokenizer-query =
        text solr.WhitespaceTokenizerFactory
    additional-schema-config =
        <copyField source="*" dest="Everything"/>

Multi-core Solr
===============

To configure Solr for multiple cores, you must use the
``collective.recipe.solrinstance:mc`` recipe. An example of a multi-core Solr
configuration could look like the following::

    [buildout]
    parts = solr-download
            solr-mc

    [solr-download]
    recipe = hexagonit.recipe.download
    strip-top-level-dir = true
    url = http://mirrorservice.nomedia.no/apache.org//lucene/solr/3.5.0/apache-solr-3.5.0.zip

    [solr-mc]
    recipe = collective.recipe.solrinstance:mc
    solr-location = ${solr-download:location}
    host = 127.0.0.1
    port = 1234
    section-name = SOLR
    directoryFactory = solr.NRTCachingDirectoryFactory
    cores = core1 core2

    [core1]
    max-num-results = 99
    unique-key = uniqueID
    index =
        name:uniqueID type:string indexed:true stored:true required:true
        name:Foo type:text copyfield:Baz
        name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true copyfield:Baz
        name:Foo bar type:text
        name:Baz type:text
        name:Everything type:text
    filter =
        text solr.LowerCaseFilterFactory
    char-filter-index =
        text solr.HTMLStripCharFilterFactory
    tokenizer-query =
        text solr.WhitespaceTokenizerFactory
        text solr.LowerCaseFilterFactory
    additional-schema-config =
        <copyField source="*" dest="Everything"/>

    [core2]
    max-num-results = 66
    unique-key = uid
    index =
        name:uid type:string indexed:true stored:true required:true
        name:La type:text
        name:Le type:date indexed:false stored:false required:true multivalued:true omitnorms:true
        name:Lau type:text
    filter =
        text solr.LowerCaseFilterFactory
    char-filter-query =
        text solr.HTMLStripCharFilterFactory
    tokenizer-index =
        text solr.WhitespaceTokenizerFactory
