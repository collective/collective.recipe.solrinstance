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

.. _Solr : http://lucene.apache.org/solr/
.. _Lucene : http://lucene.apache.org/java/docs/index.html


Note: This version of the recipe only supports Solr 3.5. Please use a release
from the 2.x series if you are using Solr 1.4.

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

jetty-template
    Optional override for the ``jetty.xml`` template. Defaults to 
    ``templates/jetty.xml.tmpl``.

logging-template
    Optional override for the ``logging.properties`` template. Defaults to
    ``templates/logging.properties.tmpl``.

jetty-destination
    Optional override for the directory where the ``jetty.xml`` file
    will be generated. Defaults to the Solr default location.

extralibs
    Optional includes of custom Java libraries. The option takes
    a path and a regular expression per line seperated by a colon.
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

Config
======

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
    Let's you enable auto commit handling and force a commit after at least
    the number of documents were added. This is disabled by default.

autoCommitMaxTime
    Let's you enable auto commit handling after a specified time in milli
    seconds. This is disabled by default.

requestParsers-multipartUploadLimitInKB
    Optional ``<requestParsers />`` parameter useful if you are submitting
    very large documents to Solr. May be the case if Solr is indexing binaries
    extracted from request.

additional-solrconfig
    Optional additional configuration to be included inside the
    ``solrconfig.xml``. For instance, ``<requestHandler />`` directives.

Cache options
+++++++++++++

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
    analysers and tokenizers, check Solr's complete reference:
    http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters

filter
    Configure the additional filters for the default field types.
    Each filter is configured on a separated line. Each line contains
    a ``index params`` pair, where ``index`` is one of the existing
    index types and ``params`` contains ``[key]:[value]`` items to
    configure the filter. Check the available filters in Solr's
    docs: http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters#TokenFilterFactories

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

Multi-core
==========

cores
    Optional. If ``collective.recipe.solrinstance:mc`` is specified for every 
    section in ``cores`` a multicore solr instance is created with it's own 
    configuration.

default-core-name
    Optional. If ``collective.recipe.solrinstance:mc`` is specified as the
    recipe, then this option controls which core is set as the default for
    incoming requests that do not specify a core name. This corresponds to
    the ``defaultCoreName`` option described at 
    http://wiki.apache.org/solr/CoreAdmin#cores.

Zope Integration
================

section-name
    Name of the product-config section to be generated for ``zope.conf``.
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

Single solr
===========

A simple example how a single solr could look like::

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
    additional-schema-config =
        <copyField source="*" dest="Everything"/>

Multicore solr
==============

To get multicore working it is needed to use 
``collective.recipe.solrinstance:mc`` recipe. A simple example how a multicore 
solr could look like::

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
