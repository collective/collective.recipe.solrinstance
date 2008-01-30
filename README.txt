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

Simple example
==============

    >>> import os

In the simplest form we can download a simple package and have it
extracted in the parts directory.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = collective.recipe.solrinstance
    ... index = name:Title type:text copyfield:default_field
    ...
    ... """)

Create the default structure. We assume the solr distribution was
downloaded before.

    >>> os.makedirs(join(sample_buildout, 'example', 'etc'))
    >>> os.makedirs(join(sample_buildout, 'example', 'solr', 'conf'))

    >>> write(sample_buildout, 'example', 'etc', 'jetty.xml',
    ... """ """)

    >>> write(sample_buildout, 'example', 'solr', 'conf', 'solr.xml',
    ... """ """)

Ok, let's run the buildout:

    >>> print system(buildout)
    Installing solr.
    jetty.xml: Generated file 'jetty.xml'.
    solrconfig.xml: Generated file 'solrconfig.xml'.
    schema.xml: Generated file 'schema.xml'.
    solr-instance: Generated script 'solr-instance'.
    <BLANKLINE>

Check, if the run script is here and the template substitution worked

   >>> cat(sample_buildout, 'bin', 'solr-instance')
   #!...
   from subprocess import Popen, call
   import sys, os
   from signal import SIGHUP
   <BLANKLINE>
   ...
   SOLR_DIR = '.../parts/solr'
   <BLANKLINE>
   ...
