Simple example
==============

    >>> import os

In the simplest form we can download a simple package and have it
extracted in the parts directory::

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... host = 127.0.0.1
    ... port = 1234
    ... max-num-results = 99
    ... section-name = SOLR
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:string indexed:true stored:true required:true
    ...     name:Foo type:text
    ...     name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    ... filter =
    ...     text solr.ISOLatin1AccentFilterFactory
    ...     text_ws Baz foo="bar" juca="bala"
    ... """)

Create the default structure. We assume the solr distribution was
downloaded before::

    >>> os.makedirs(join(sample_buildout, 'example', 'etc'))
    >>> os.makedirs(join(sample_buildout, 'example', 'solr', 'conf'))

Ok, let's run the buildout::

    >>> print system(buildout)
    Installing solr.
    jetty.xml: Generated file 'jetty.xml'.
    solrconfig.xml: Generated file 'solrconfig.xml'.
    schema.xml: Generated file 'schema.xml'.
    solr-instance: Generated script 'solr-instance'.

Check if the run script is here and the template substitution worked::

    >>> cat(sample_buildout, 'bin', 'solr-instance')
    #!...
    from subprocess import Popen, call
    import sys, os
    from signal import SIGHUP
    ...
    SOLR_DIR = '.../parts/solr'
    ...

Also check that the XML files are where we expect them to be::

    >>> ls(sample_buildout, 'parts', 'solr', 'etc')
    -  jetty.xml

    >>> ls(sample_buildout, 'parts', 'solr', 'solr', 'conf')
    -  schema.xml
    -  solrconfig.xml

And make sure the substitution worked for all files.

`jetty.xml`::

    >>> cat(sample_buildout, 'parts', 'solr', 'etc', 'jetty.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <Set name="port">1234</Set>
    ...
    <Arg>.../var/solr/log/jetty-yyyy_mm_dd.request.log</Arg>
    ...

`schema.xml`::

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <filter class="Baz" foo="bar" juca="bala"/>
    ...
    <filter class="solr.ISOLatin1AccentFilterFactory" />
    ...
    <field name="uniqueID" type="string" indexed="true" stored="true" required="true" ... />
    <field name="Foo" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           omitNorms="false" />
    <field name="Bar" type="date" indexed="false"
           stored="false" required="true" multiValued="true"
           omitNorms="true" />
    ...
    <uniqueKey>uniqueID</uniqueKey>
    ...

`solrconfig.xml`::

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <dataDir>.../var/solr/data</dataDir>
    ...
    <int name="rows">99</int>
    ...

Let's check that the zope-conf snippet was correctly generated::

    >>> cat(sample_buildout, '.installed.cfg')
    [buildout]
    ...
    zope-conf =
        <product-config SOLR>
        ...address 127.0.0.1:1234
        ...basepath /solr
        </product-config>

Finally, test the error handling as well:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... unique-key = uniqueID
    ... index =
    ...     name:Foo type:text
    ... """)
    >>> print system(buildout)
    Uninstalling solr.
    ...
    Error: Unique key without matching index: uniqueID

We need to remove the "solr" part before re-running the the buildout, which
is a bit stupid, but oh well:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:text
    ...     name:Foo type:text
    ... """)
    >>> print system(buildout)
    Installing solr.
    ...
    Error: Unique key needs to be declared "required": uniqueID

A default search field can also be specified, but this also requires the
matching index to be set up:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... default-search-field = Foo
    ... unique-key =
    ... index =
    ... """)
    >>> print system(buildout)
    Installing solr.
    ...
    Error: Default search field without matching index: Foo

With the index set up correctly, things work again:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... default-search-field = Foo
    ... unique-key =
    ... index =
    ...     name:Foo type:text
    ... """)
    >>> print system(buildout)
    Installing solr.
    jetty.xml: Generated file 'jetty.xml'.
    solrconfig.xml: Generated file 'solrconfig.xml'.
    schema.xml: Generated file 'schema.xml'.
    solr-instance: Generated script 'solr-instance'.
    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <defaultSearchField>Foo</defaultSearchField>
    ...

There's no default for the default search field, however:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... unique-key =
    ... index =
    ... """)
    >>> print system(buildout)
    Uninstalling solr.
    Installing solr.
    jetty.xml: Generated file 'jetty.xml'.
    solrconfig.xml: Generated file 'solrconfig.xml'.
    schema.xml: Generated file 'schema.xml'.
    solr-instance: Generated script 'solr-instance'.

    >>> def read(*path):
    ...     return open(os.path.join(*path)).read()
    >>> schema = read(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    >>> schema.index('<defaultSearchField>')
    Traceback (most recent call last):
    ...
    ValueError: substring not found

