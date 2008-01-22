Supported options
=================

The recipe supports the following options:

solr-location
    Path to the location of the Solr installation. This
    should be the top-level installation directory.

address
    Address of the Solr server, e.g. some.server.com.

port
    Server port.

basepath
    Base path to the Solr service on the server. The final URL to the
    Solr service will be made of

       ``$address:$port/$basepath``

    to which the actual commands will be appended.

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

max-num-results
    The maximum number of results the Solr server returns. Defaults to 10.
