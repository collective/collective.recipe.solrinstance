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

schema-destination
    Optional override for the directory where the ``schema.xml`` file
    will be generated. Defaults to the Solr default location.

jetty-destination
    Optional override for the directory where the ``jetty.xml`` file
    will be generated. Defaults to the Solr default location.

index
    Configures the different types of index fields provided by the
    Solr instance. Each field is configured on a separated line. Each
    line contains a white-space separated list of ``[key]:[value]``
    pairs which define the index.

filter
    Configure the additional filters for each index type. Each filter
    is configured on a separated line. Each line contains a
    ``index params`` pair, where ``ìndex`` is one of the existing
    index types and ``params`` contains ``[key]:[value]`` items to
    configure the filter. Check the available filters in Solr's
    docs: http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters

max-num-results
    The maximum number of results the Solr server returns. Defaults to 10.

section-name
    Name of the product-config section to be generated for ``zope.conf``.
    Defaults to 'solr'.

zope-conf
    Optional override for the configuration snippet that is generated to
    be included in ``zope.conf`` by other recipes. Defaults to:

        <product-config ${part:section-name}>
            address ${part:host}:${part:port}
            basepath ${part:basepath}
        </product-config>
