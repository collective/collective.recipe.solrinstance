**************************************
Recipe for configuring a Solr instance
**************************************

.. contents::

The recipe configures an instance of the Solr_ indexing server. Solr
is an open source enterprise search server based on the Lucene_ Java
search library, with XML/HTTP and JSON APIs, hit highlighting, faceted
search, caching, replication, and a web administration interface

SVN Repository: http://svn.plone.org/svn/collective/buildout/collective.recipe.solrinstance/

.. _Solr : http://lucene.apache.org/solr/
.. _Lucene : http://lucene.apache.org/java/docs/index.html


Note: This version of the recipe only supports Solr 1.4. Please use a release
from the 0.x series if you are using Solr 1.3.


Supported options
=================

The recipe supports the following options:

solr-location
    Path to the location of the Solr installation. This should be
    the top-level installation directory.

host
    Name or IP address of the Solr server, e.g. some.server.com.
    Defaults to 'localhost'.

port
    Server port. Defaults to 8983.

basepath
    Base path to the Solr service on the server. The final URL to the
    Solr service will be made of

       ``$host:$port/$basepath``

    to which the actual commands will be appended. Defaults to '/solr'.

config-destination
    Optional override for the directory where the ``solrconfig.xml``
    file will be generated. Defaults to the Solr default location.

config-template
    Optional override for the template used to generate the ``solrconfig.xml``
    file. Defaults to the template contained in the recipe, i.e.
    ``templates/solrconfig.xml.tmpl``.

schema-destination
    Optional override for the directory where the ``schema.xml`` file
    will be generated. Defaults to the Solr default location.

schema-template
    Optional override for the template used to generate the ``schema.xml``
    file. Defaults to the template contained in the recipe, i.e.
    ``templates/schema.xml.tmpl``.

jetty-destination
    Optional override for the directory where the ``jetty.xml`` file
    will be generated. Defaults to the Solr default location.

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
    pairs which define the index.

unique-key
    Optional override for declaring a field to be unique for all documents.
    See http://wiki.apache.org/solr/SchemaXml for more information
    Defaults to 'uid'.

default-search-field
    Configure a default search field, which is used when no field was
    explicitly given. See http://wiki.apache.org/solr/SchemaXml.

max-num-results
    The maximum number of results the Solr server returns. Defaults to 10.

section-name
    Name of the product-config section to be generated for ``zope.conf``.
    Defaults to 'solr'.

zope-conf
    Optional override for the configuration snippet that is generated to
    be included in ``zope.conf`` by other recipes. Defaults to::

        <product-config ${part:section-name}>
            address ${part:host}:${part:port}
            basepath ${part:basepath}
        </product-config>

default-operator
    The default operator to use for queries.  Valid values or AND and OR.
    Defaults to OR.

additional-solrconf
    Optional additional configuration to be included inside the
    solrconfig.xml. For instance, ``<requestHandler />`` directives.

cacheSize
    Number of cache entries for the various caches (filterCache,
    fieldValueCache, queryResultCache and documentCache). Defaults to ``512``.

maxWarmingSearchers
    Maximum number of searchers that may be warming in the background.
    Defaults to 4. For read-only slaves recommend to set to 1 or 2.

useColdSearcher
    If a request comes in without a warm searcher available, immediately use
    one of the warming searchers to handle the request. Defaults to ``false``.

requestParsers-multipartUploadLimitInKB
    Optional ``<requestParsers />`` parameter useful if you are submitting
    very large documents to Solr. May be the case if Solr is indexing binaries
    extracted from request.

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
