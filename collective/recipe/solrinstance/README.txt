Simple example
==============

Testing single solr instance
----------------------------

    >>> import os

In the simplest form we can download a simple package and have it
extracted in the parts directory:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... host = 127.0.0.1
    ... port = 1234
    ... max-num-results = 99
    ... section-name = SOLR
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:string indexed:true stored:true required:true
    ...     name:Foo type:text copyfield:Baz
    ...     name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true copyfield:Baz
    ...     name:Foo bar type:text
    ...     name:Baz type:text
    ...     name:Everything type:text
    ... tokenizer =
    ...     text solr.KeywordTokenizerFactory
    ... filter =
    ...     text solr.ISOLatin1AccentFilterFactory
    ...     text_ws Baz foo="bar" juca="bala"
    ... char-filter =
    ...     text solr.HTMLStripCharFilterFactory
    ... additional-schema-config =
    ...      <copyField source="*" dest="Everything"/>
    ... extra-conf-files =
    ...      extra/foo.txt
    ...      extra/bar.txt
    ... """.format(sample_buildout))

Create extra files:

    >>> os.makedirs(join(sample_buildout, 'extra'))
    >>> open(join(sample_buildout, 'extra', 'foo.txt'), 'w').close()
    >>> open(join(sample_buildout, 'extra', 'bar.txt'), 'w').close()

Create the default structure. We assume the solr distribution was
downloaded before:

    >>> os.makedirs(join(sample_buildout, 'example', 'etc'))
    >>> os.makedirs(join(sample_buildout, 'example', 'solr', 'conf'))
    >>> os.makedirs(join(sample_buildout, 'dist'))
    >>> os.makedirs(join(sample_buildout, 'contrib'))
    >>> open(join(sample_buildout, 'example', 'solr', 'conf', 'test1.txt'), 'w').close()
    >>> open(join(sample_buildout, 'example', 'solr', 'conf', 'test2.txt'), 'w').close()

Ok, let's run the buildout:

    >>> print(system(buildout))
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

Check if the run script is here and the template substitution worked:

    >>> cat(sample_buildout, 'bin', 'solr-instance')
    #!...
    from subprocess import Popen, call
    import atexit
    import signal
    import sys, os
    ...
    SOLR_DIR = r'.../parts/solr'
    ...
    START_CMD = ['java', '-jar', 'start.jar']
    UPDATE_URL = r'http://127.0.0.1:1234/solr/update'
    ...

Also check that the XML files are where we expect them to be:

    >>> ls(sample_buildout, 'parts', 'solr', 'etc')
    -  jetty.xml
    -  log4j.properties
    -  logging.properties

    >>> ls(sample_buildout, 'parts', 'solr', 'solr', 'conf')
    -  bar.txt
    -  foo.txt
    -  schema.xml
    -  solrconfig.xml
    -  stopwords.txt
    -  synonyms.txt
    -  test1.txt
    -  test2.txt

And make sure the substitution worked for all files.

`jetty.xml`:

    >>> cat(sample_buildout, 'parts', 'solr', 'etc', 'jetty.xml')
    <?xml version="1.0"?>
    ...
    <Set name="port">1234</Set>
    ...

`schema.xml`:

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <filter class="Baz" foo="bar" juca="bala"/>
    ...
    <charFilter class="solr.HTMLStripCharFilterFactory" />
    ...
    <filter class="solr.ISOLatin1AccentFilterFactory" />
    ...
    <tokenizer class="solr.KeywordTokenizerFactory" />
    ...
    <field name="uniqueID" type="string" indexed="true"
           stored="true" required="true" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    <field name="Foo" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    <field name="Bar" type="date" indexed="false"
           stored="false" required="true" multiValued="true"
           omitNorms="true" termVectors="false"
           termPositions="false" termOffsets="false"/>
    <field name="Foo bar" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    <field name="Baz" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    <field name="Everything" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    ...
    <uniqueKey>uniqueID</uniqueKey>
    ...
    <copyField source="Foo" dest="Baz"/>
    <copyField source="Bar" dest="Baz"/>
    ...
    <copyField source="*" dest="Everything"/>
    ...

`solrconfig.xml`:

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <dataDir>.../var/solr/data</dataDir>
    ...
    <int name="rows">99</int>
    ...

`stopwords.txt`:

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'stopwords.txt')
    # Standard english stop words taken from Lucene's StopAnalyzer
    a
    an
    ...


Let's check that the zope-conf snippet was correctly generated:

    >>> cat(sample_buildout, '.installed.cfg')
    [buildout]
    ...
    zope-conf =
        <product-config SOLR>
        ...address 127.0.0.1:1234
        ...basepath /solr
        </product-config>

Finally, test the error handling as well, for example specifying the optional
unique key.  Without a matching index this yields an error, though:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key = uniqueID
    ... index =
    ...     name:Foo type:text
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    ...
    Error: Unique key without matching index: uniqueID

Files should support Unicode output if present in templates::

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'unicode_test.xml',
    ... """<schema>
    ... <!-- Mønti Pythøn ik den Hølie Gräilen. A Møøse once bit my sister... -->
    ... </schema>""")
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = unicode_test.xml
    ... unique-key =
    ... index =
    ... """.format(sample_buildout))

    >>> print(system(buildout))
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <schema>
    <!-- Mønti Pythøn ik den Hølie Gräilen. A Møøse once bit my sister... -->
    </schema>


If a unique key was specified, it'll also be mandatory to pass it in, i.e.
the index needs to be declared to be "required".  Aside from that, we need
to remove the "solr" part before re-running the the buildout, which is a
bit stupid, but oh well:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:text
    ...     name:Foo type:text
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    ...
    Error: Unique key needs to declared "required"=true or "default"=NEW: uniqueID

If no unique key was specified in the first place, the tag shouldn't appear
in the generated xml either:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key =
    ... index =
    ...     name:Foo type:text
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Installing solr.
    ...
    >>> def read(*path):
    ...     return open(os.path.join(*path)).read()
    >>> schema = read(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    >>> schema.index('<uniqueKey>')
    Traceback (most recent call last):
    ...
    ValueError: substring not found

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
    ... solr-version = 3
    ... solr-location = {0}
    ... default-search-field = Foo
    ... unique-key =
    ... index =
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
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
    ... solr-version = 3
    ... solr-location = {0}
    ... default-search-field = Foo
    ... unique-key =
    ... index =
    ...     name:Foo type:text
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

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
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key =
    ... index =
    ... """.format(sample_buildout))

    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> schema = read(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    >>> schema.index('<defaultSearchField>')
    Traceback (most recent call last):
    ...
    ValueError: substring not found

You can also define extra field types:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key =
    ... extra-field-types =
    ...     <fieldType name="foo_type" class="FooField"/>
    ...     <fieldType name="bar_type" class="BarField">
    ...         <analyzer type="index">
    ...             <tokenizer class="BarTokenizer"/>
    ...         </analizer>
    ...     </fieldType>
    ... index =
    ...     name:Foo type:foo_type
    ...     name:Bar type:bar_type
    ... """.format(sample_buildout))

    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <types>
    ...
    <fieldType name="foo_type" class="FooField"/>
    <fieldType name="bar_type" class="BarField">
    <analyzer type="index">
    <tokenizer class="BarTokenizer"/>
    </analizer>
    </fieldType>
    ...
    <fields>
    ...
    <field name="Foo" type="foo_type" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    <field name="Bar" type="bar_type" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    ...

For more complex setups it's also possible to specify an alternative template
to be used to generate `schema.xml`:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'alt_schema.xml',
    ... """<schema>
    ... schema here
    ... </schema>""")
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = alt_schema.xml
    ... unique-key =
    ... index =
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <schema>
    schema here
    </schema>

When used custom index attributes should be allowed as they might make sense
in some situations. Any additional attributes are collected in a special
variable that can then be conveniently used in the template:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'schema.xml',
    ... """<schema name="foo">
    ... {% for index in options.indeces %}\
    ... <field name="${index.name}" ${index.extras} />
    ... {% end %}
    ... </schema>""")
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = schema.xml
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar another:one
    ...     name:Bar type:text
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'schema.xml')
    <schema name="foo">
    <field name="Foo" another="one" foo="bar" />
    <field name="Bar" />
    </schema>

Without the custom template for `schema.xml` this should yield an error:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    ...
    Error: Invalid index attribute(s): foo. Allowed attributes are: ...

Additional solrconfig should also be allowed:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = schema.xml
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar another:one
    ...     name:Bar type:text
    ... additional-solrconfig =
    ...     <foo attr="value1">
    ...         <bar />
    ...     </foo>
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <foo attr="value1">
        <bar />
    </foo>
    ...

Additional solrconfig query section should also be allowed:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = schema.xml
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar another:one
    ...     name:Bar type:text
    ... additional-solrconfig-query =
    ...     <listener event="firstSearcher">
    ...         <arr />
    ...     </listener>
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <listener event="firstSearcher">
        <arr />
    </listener>
    </query>
    ...

Sometimes it is necessary to include extra libraries (e.g. DIH-handler,
solr-cell, ...). You can do this with the `extralibs`-option.

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key = Foo
    ... index =
    ...     name:Foo type:text required:true
    ... extralibs =
    ...      /foo/bar:.*\.jarx
    ...      /my/lava/libs
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
      <lib dir="/foo/bar" regex=".*\.jarx" />
      <lib dir="/my/lava/libs" regex=".*\.jar" />
    ...

Test autoCommit arguments:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = schema.xml
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar another:one
    ... autoCommitMaxDocs = 1000
    ... autoCommitMaxTime = 900000
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <autoCommit>
    <maxDocs>1000</maxDocs>
    <maxTime>900000</maxTime>
    </autoCommit>
    ...

Testing the request parsers default limit:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = schema.xml
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar another:one
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <requestParsers enableRemoteStreaming="false" multipartUploadLimitInKB="102400" />
    ...

Test changing the request parsers limit:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... schema-template = schema.xml
    ... unique-key =
    ... index =
    ...     name:Foo type:text foo:bar another:one
    ... requestParsers-multipartUploadLimitInKB = 4096
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <requestParsers enableRemoteStreaming="false" multipartUploadLimitInKB="4096" />
    ...

For more complex configuration requirements, it's also possible to specify an
alternative template to be used to generate `solrconfig.xml`:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'alt_solrconfig.xml',
    ... """<config>
    ... configure me here
    ... </config>""")
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... config-template = alt_solrconfig.xml
    ... unique-key =
    ... index =
    ... """.format(sample_buildout))
    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
    <config>
    configure me here
    </config>

The ``vardir`` option lets you override the location of the Solr data
files. The ``script`` option lets you override the name of the generated
script (normally "solr-instance"); provide an empty script name to not
generate the script. These options make it possible for multiple
Solr instances to coexist in a single buildout:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> rmdir(sample_buildout, 'var')
    >>> remove(sample_buildout, 'bin', 'solr-instance')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr-main solr-functest
    ...
    ... [solr-main]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key =
    ... index =
    ... vardir = ${{buildout:directory}}/var/solr-main
    ... script = solr-main
    ...
    ... [solr-functest]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... unique-key =
    ... index =
    ... vardir = ${{buildout:directory}}/var/solr-functest
    ... script =
    ... """.format(sample_buildout))

    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr-main.
    solr-main: Generated file 'jetty.xml'.
    solr-main: Generated file 'log4j.properties'.
    solr-main: Generated file 'logging.properties'.
    solr-main: Generated script 'solr-main'.
    solr-main: Generated file 'solrconfig.xml'.
    solr-main: Generated file 'schema.xml'.
    solr-main: Generated file 'stopwords.txt'.
    solr-main: Generated file 'synonyms.txt'.
    Installing solr-functest.
    solr-functest: Generated file 'jetty.xml'.
    solr-functest: Generated file 'log4j.properties'.
    solr-functest: Generated file 'logging.properties'.
    solr-functest: Generated file 'solrconfig.xml'.
    solr-functest: Generated file 'schema.xml'.
    solr-functest: Generated file 'stopwords.txt'.
    solr-functest: Generated file 'synonyms.txt'.

    >>> ls(sample_buildout, 'var')
    d  solr-functest
    d  solr-main
    >>> ls(sample_buildout, 'bin')
    -  buildout
    -  solr-main

Testing the java_opts optional params:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 3
    ... solr-location = {0}
    ... host = 127.0.0.1
    ... port = 1234
    ... max-num-results = 99
    ... section-name = SOLR
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:string indexed:true stored:true required:true
    ... java_opts =
    ...     -Xms512M
    ...     -Xmx1024M
    ... """.format(sample_buildout))

Ok, let's run the buildout:

    >>> print(system(buildout))
    Uninstalling solr-functest.
    Uninstalling solr-main.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solrconfig.xml'.
    solr: Generated file 'schema.xml'.
    solr: Generated file 'stopwords.txt'.
    solr: Generated file 'synonyms.txt'.

Check if the run script is here and the template substitution worked
with java_opts:

    >>> cat(sample_buildout, 'bin', 'solr-instance')
    #!...
    from subprocess import Popen, call
    import atexit
    import signal
    import sys, os
    ...
    START_CMD = ['java', '-jar', '-Xms512M', '-Xmx1024M', 'start.jar']
    ...

Testing multicore
-----------------

Testing multicore recipe without cores:

    >>> rmdir(sample_buildout, 'parts', 'solr')
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr-mc
    ...
    ... [solr-mc]
    ... recipe = collective.recipe.solrinstance:mc
    ... solr-version = 3
    ... solr-location = {0}
    ... host = 127.0.0.1
    ... port = 1234
    ... max-num-results = 99
    ... section-name = SOLR
    ... java_opts =
    ...     -Xms512M
    ...     -Xmx1024M
    ... """.format(sample_buildout))

Ok, let's run the buildout:

    >>> print(system(buildout))
    Uninstalling solr.
    Installing solr-mc.
    While:
      Installing solr-mc.
    Error: Missing option: solr-mc:cores

Testing multicore recipe with wrong cores:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr-mc
    ...
    ... [solr-mc]
    ... recipe = collective.recipe.solrinstance:mc
    ... solr-version = 3
    ... solr-location = {0}
    ... host = 127.0.0.1
    ... cores =
    ... port = 1234
    ... max-num-results = 99
    ... section-name = SOLR
    ... java_opts =
    ...     -Xms512M
    ...     -Xmx1024M
    ... """.format(sample_buildout))

Ok, let's run the buildout:

    >>> print(system(buildout))
    Installing solr-mc.
    While:
      Installing solr-mc.
    Error: Attribute `cores` is not correctly defined. Define as a whitespace
    or line separated list like `cores = X1 X2 X3`


Note that you can specify the ``cores`` option as either newline separated or
other whitespace separated.

Test our first core:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr-mc
    ...
    ... [solr-mc]
    ... recipe = collective.recipe.solrinstance:mc
    ... solr-version = 3
    ... solr-location = {0}
    ... host = 127.0.0.1
    ... port = 1234
    ... section-name = SOLR
    ... cores = core1 core2
    ... java_opts =
    ...     -Xms512M
    ...     -Xmx1024M
    ...
    ... [core1]
    ... max-num-results = 55
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:uuid indexed:true stored:true default:NEW
    ...     name:Foo type:text
    ...     name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    ...     name:Foo bar type:text
    ...     name:BlaWS type:text_ws
    ... char-filter =
    ...     text_ws solr.HTMLStripCharFilterFactory
    ... char-filter-index =
    ...     text_ws solr.MappingCharFilterFactory mapping="my-mapping.txt"
    ... filter =
    ...     text solr.ISOLatin1AccentFilterFactory
    ...     text_ws Baz foo="bar" juca="bala"
    ... filter-index =
    ...     text solr.LowerCaseFilterFactory
    ... filter-query =
    ...     text solr.LowerCaseFilterFactory
    ...     text solr.PorterStemFilterFactory
    ... tokenizer-index =
    ...     text solr.StandardTokenizerFactory
    ... tokenizer-query =
    ...     text solr.StandardTokenizerFactory
    ...     text solr.WhitespaceTokenizerFactory
    ... extra-conf-files =
    ...      extra/foo.txt
    ...      extra/bar.txt
    ...
    ... [core2]
    ... max-num-results = 99
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:uuid indexed:true stored:true default:NEW
    ...     name:Foo type:text
    ...     name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    ...     name:Foo bar type:text
    ... char-filter =
    ...     text_ws solr.HTMLStripCharFilterFactory
    ... char-filter-index =
    ...     text_ws solr.MappingCharFilterFactory mapping="my-mapping.txt"
    ... filter =
    ...     text solr.ISOLatin1AccentFilterFactory
    ...     text_ws Baz foo="bar" juca="bala"
    ... filter-index =
    ...     text solr.LowerCaseFilterFactory
    ... filter-query =
    ...     text solr.LowerCaseFilterFactory
    ...     text solr.PorterStemFilterFactory
    ... tokenizer-index =
    ...     text solr.StandardTokenizerFactory
    ... tokenizer-query =
    ...     text solr.StandardTokenizerFactory
    ...     text solr.WhitespaceTokenizerFactory
    ... """.format(sample_buildout))

Ok, let's run the buildout:

    >>> print(system(buildout))
    Installing solr-mc.
    solr-mc: Generated file 'jetty.xml'.
    solr-mc: Generated file 'log4j.properties'.
    solr-mc: Generated file 'logging.properties'.
    solr-mc: Generated script 'solr-instance'.
    solr-mc: Generated file 'solr.xml'.
    core1: Generated file 'solrconfig.xml'.
    core1: Generated file 'schema.xml'.
    core1: Generated file 'stopwords.txt'.
    core1: Generated file 'synonyms.txt'.
    core2: Generated file 'solrconfig.xml'.
    core2: Generated file 'schema.xml'.
    core2: Generated file 'stopwords.txt'.
    core2: Generated file 'synonyms.txt'.

See if there are all needed files:

    >>> ls(sample_buildout, 'parts', 'solr-mc', 'solr')
    d  core1
    d  core2
    -  solr.xml

See if there is ``solr.xml``:

    >>> cat(sample_buildout, 'parts', 'solr-mc', 'solr', 'solr.xml')
    <?xml...
    <solr persistent="true">
    ...
      <cores adminPath="/admin/cores">
        <core name="core1" instanceDir="core1" />
        <core name="core2" instanceDir="core2" />
      </cores>
    ...

See if there are all needed files in `core1`:

    >>> ls(sample_buildout, 'parts', 'solr-mc', 'solr', 'core1', 'conf')
    - bar.txt
    - foo.txt
    - schema.xml
    - solrconfig.xml
    - stopwords.txt
    - synonyms.txt
    - test1.txt
    - test2.txt

See if there are all needed files in `core2`:

    >>> ls(sample_buildout, 'parts', 'solr-mc', 'solr', 'core2', 'conf')
    - schema.xml
    - solrconfig.xml
    - stopwords.txt
    - synonyms.txt
    - test1.txt
    - test2.txt

See if name is set in `schema.xml`:

    >>> cat(sample_buildout, 'parts', 'solr-mc', 'solr', 'core1', 'conf', 'schema.xml')
    <?xml...
    <schema ...
    <fieldType name="text_ws" class="solr.TextField" positionIncrementGap="100"...
      <analyzer type="index">
        <charFilter class="solr.HTMLStripCharFilterFactory" />
        <charFilter class="solr.MappingCharFilterFactory" mapping="my-mapping.txt"/>
        <tokenizer class="solr.WhitespaceTokenizerFactory" />
        <filter class="Baz" foo="bar" juca="bala"/>
      </analyzer>
      <analyzer type="query">
        <charFilter class="solr.HTMLStripCharFilterFactory" />
        <tokenizer class="solr.WhitespaceTokenizerFactory" />
        <filter class="Baz" foo="bar" juca="bala"/>
      </analyzer>
    </fieldType>...
    <fieldType name="text" class="solr.TextField" positionIncrementGap="100"...
      <analyzer type="index">
        <tokenizer class="solr.StandardTokenizerFactory" />
        <filter class="solr.ISOLatin1AccentFilterFactory" />
        <filter class="solr.LowerCaseFilterFactory" />
      </analyzer>
      <analyzer type="query">
        <tokenizer class="solr.WhitespaceTokenizerFactory" />
        <filter class="solr.ISOLatin1AccentFilterFactory" />
        <filter class="solr.LowerCaseFilterFactory" />
        <filter class="solr.PorterStemFilterFactory" />
      </analyzer>
    </fieldType>
    ...
    <field name="BlaWS" type="text_ws" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"/>
    ...

You can specify a default core with ``default-core-name``:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr-mc
    ...
    ... [solr-mc]
    ... recipe = collective.recipe.solrinstance:mc
    ... solr-version = 3
    ... solr-location = {0}
    ... cores =
    ...     core1
    ...     core2
    ... default-core-name = core1
    ...
    ... [core1]
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:uuid indexed:true stored:true default:NEW
    ...
    ... [core2]
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:uuid indexed:true stored:true default:NEW
    ... """.format(sample_buildout))

Ok, let's run the buildout:

    >>> print(system(buildout))
    Uninstalling solr-mc.
    Installing solr-mc.
    solr-mc: Generated file 'jetty.xml'.
    solr-mc: Generated file 'log4j.properties'.
    solr-mc: Generated file 'logging.properties'.
    solr-mc: Generated script 'solr-instance'.
    solr-mc: Generated file 'solr.xml'.
    core1: Generated file 'solrconfig.xml'.
    core1: Generated file 'schema.xml'.
    core1: Generated file 'stopwords.txt'.
    core1: Generated file 'synonyms.txt'.
    core2: Generated file 'solrconfig.xml'.
    core2: Generated file 'schema.xml'.
    core2: Generated file 'stopwords.txt'.
    core2: Generated file 'synonyms.txt'.

The parameter should thus end up in ``solr.xml``:

    >>> cat(sample_buildout, 'parts', 'solr-mc', 'solr', 'solr.xml')
    <?xml...
    <solr persistent="true">
    ...
      <cores adminPath="/admin/cores" defaultCoreName="core1">
        <core name="core1" instanceDir="core1" />
        <core name="core2" instanceDir="core2" />
      </cores>
    ...

Regeneration of files
~~~~~~~~~~~~~~~~~~~~~

Files should regenerate whenever Buildout is re-run and the underlying cores
have changed. We'll create a basic configuration, run it, modify the result
and make sure regeneration happens when it should.

    >>> configuration = """
    ... [buildout]
    ... parts = solr-mc
    ...
    ... [solr-mc]
    ... recipe = collective.recipe.solrinstance:mc
    ... solr-version = 3
    ... solr-location = {0}
    ... cores =
    ...     core1
    ...     core2
    ... default-core-name = core1
    ...
    ... [core1]
    ... unique-key = {1}
    ... index =
    ...     name:{1} type:string indexed:true stored:true required:true
    ...
    ... [core2]
    ... unique-key = {2}
    ... index =
    ...     name:{2} type:string indexed:true stored:true required:true
    ... """

    >>> write(sample_buildout, 'buildout.cfg',
    ...       configuration.format(sample_buildout, 'value1', 'value2'))
    >>> print(system(buildout))
    Updating solr-mc.

Firstly, make no changes. No files should be regenerated.

    >>> write(sample_buildout, 'buildout.cfg',
    ...       configuration.format(sample_buildout, 'value1', 'value2'))
    >>> print(system(buildout))
    Updating solr-mc.

Now, modify one of the cores to ensure the configuration is regenerated.

    >>> write(sample_buildout, 'buildout.cfg',
    ...       configuration.format(sample_buildout, 'value1', 'value3'))
    >>> print(system(buildout))
    Updating solr-mc.

Modify both cores and ensure configuration is still regenerated.

    >>> write(sample_buildout, 'buildout.cfg',
    ...       configuration.format(sample_buildout, 'value2', 'value4'))
    >>> print(system(buildout))
    Updating solr-mc.

Finally, re-run with both values changed to ensure no regeneration happens.

    >>> write(sample_buildout, 'buildout.cfg',
    ...       configuration.format(sample_buildout, 'value2', 'value4'))
    >>> print(system(buildout))
    Updating solr-mc.

Test Solr4
----------

Test solr 4 templates.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... solr-version = 4
    ... solr-location = {0}
    ... host = 127.0.0.1
    ... port = 1234
    ... max-num-results = 99
    ... section-name = SOLR
    ... unique-key = uniqueID
    ... index =
    ...     name:uniqueID type:string indexed:true stored:true required:true
    ...     name:Foo type:text copyfield:Baz
    ...     name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true copyfield:Baz
    ...     name:Foo bar type:text
    ...     name:Baz type:text
    ...     name:Everything type:text
    ...     name:Fisch type:text storeOffsetsWithPositions:true
    ... """.format(sample_buildout))

Indicate that we are using solr4 (collection1):

    >>> os.makedirs(join(sample_buildout, 'example', 'solr', 'collection1'))
    >>> os.makedirs(join(sample_buildout, 'example', 'solr', 'collection1', 'conf'))

Ok, let's run the buildout:

    >>> print(system(buildout))
    Uninstalling solr-mc.
    Installing solr.
    solr: Generated file 'jetty.xml'.
    solr: Generated file 'log4j.properties'.
    solr: Generated file 'logging.properties'.
    solr: Generated script 'solr-instance'.
    solr: Generated file 'solr.xml'.
    collection1: Generated file 'solrconfig.xml'.
    collection1: Generated file 'schema.xml'.
    collection1: Generated file 'stopwords.txt'.
    collection1: Generated file 'synonyms.txt'.

Also check that the XML files are where we expect them to be:

    >>> ls(sample_buildout, 'parts', 'solr', 'etc')
    -  jetty.xml
    -  log4j.properties
    -  logging.properties

    >>> ls(sample_buildout, 'parts', 'solr', 'solr', 'collection1' , 'conf')
    -  schema.xml
    -  solrconfig.xml
    -  stopwords.txt
    -  synonyms.txt
    -  test1.txt
    -  test2.txt

`schema.xml`:

    >>> cat(sample_buildout, 'parts', 'solr', 'solr', 'collection1', 'conf', 'schema.xml')
    <?xml version="1.0" encoding="UTF-8" ?>
    ...
    <field name="uniqueID" type="string" indexed="true"
           stored="true" required="true" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"
    />
    <field name="Foo" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"
    />
    <field name="Bar" type="date" indexed="false"
           stored="false" required="true" multiValued="true"
           omitNorms="true" termVectors="false"
           termPositions="false" termOffsets="false"
    />
    <field name="Foo bar" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"
    />
    <field name="Baz" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"
    />
    <field name="Everything" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false"
    />
    <field name="Fisch" type="text" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="false" termPositions="false"
           termOffsets="false" storeOffsetsWithPositions="true"
    />
    ...
    <uniqueKey>uniqueID</uniqueKey>
    ...
    <copyField source="Foo" dest="Baz"/>
    <copyField source="Bar" dest="Baz"/>
    ...

That's all folks!
