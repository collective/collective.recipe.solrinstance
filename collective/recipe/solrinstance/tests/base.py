# -*- coding: utf-8 -*-
from contextlib import contextmanager
from os.path import join
from zc.buildout.testing import buildoutSetUp
from zc.buildout.testing import buildoutTearDown
from zc.buildout.testing import install_develop
import sys

if sys.version_info <= (2, 7):
    import unittest2 as unittest  # for py2.6
else:
    import unittest

BASE_CONF = """\
[buildout]
parts = solr

[solr]
recipe = collective.recipe.solrinstance{addon:s}
"""

SINGLE_CORE_CONF = """\
[buildout]
parts = solr

[solr]
recipe = collective.recipe.solrinstance{addon:s}
host = 127.0.0.1
port = 1234
max-num-results = 99
section-name = SOLR
unique-key = uniqueID
index =
    name:uniqueID type:string indexed:true stored:true required:true
    # You can add comment lines among index definitions
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo bar type:text

additionalFieldConfig =
   <dynamicField name="*_public" type="string" indexed="true" stored="true"  multiValued="true"/>
   <dynamicField name="*_restricted" type="string" indexed="true" stored="true"  multiValued="true"/>

char-filter =
    text_ws solr.HTMLStripCharFilterFactory
char-filter-index =
    text_ws solr.MappingCharFilterFactory mapping="my-mapping.txt"
filter =
    text solr.ISOLatin1AccentFilterFactory
    text_ws Baz foo="bar" juca="bala"
filter-index =
    text solr.LowerCaseFilterFactory
filter-query =
    text solr.LowerCaseFilterFactory
    text solr.PorterStemFilterFactory
tokenizer-index =
    text solr.StandardTokenizerFactory
tokenizer-query =
    text solr.StandardTokenizerFactory
    text solr.WhitespaceTokenizerFactory
"""  # noqa

MULTICORE_CONF = """\
[buildout]
parts = solr-mc

[solr-mc]
recipe = collective.recipe.solrinstance:mc{addon:s}
host = 127.0.0.1
port = 1234
section-name = SOLR
cores = core1 core2
directoryFactory = solr.RAMDirectoryFactory
java_opts =
    -Xms512M
    -Xmx1024M

[core1]
max-num-results = 55
unique-key = uniqueID
directoryFactory = solr.StandardDirectoryFactory
index =
    name:uniqueID type:uuid indexed:true stored:true default:NEW
    # You can add comment lines among index definitions
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo bar type:text
    name:BlaWS type:text_ws

additionalFieldConfig =
   <dynamicField name="*_public" type="string" indexed="true" stored="true"  multiValued="true"/>
   <dynamicField name="*_restricted" type="string" indexed="true" stored="true"  multiValued="true"/>

char-filter =
    text_ws solr.HTMLStripCharFilterFactory
char-filter-index =
    text_ws solr.MappingCharFilterFactory mapping="my-mapping.txt"
filter =
    text solr.ISOLatin1AccentFilterFactory
    text_ws Baz foo="bar" juca="bala"
filter-index =
    text solr.LowerCaseFilterFactory
filter-query =
    text solr.LowerCaseFilterFactory
    text solr.PorterStemFilterFactory
tokenizer-index =
    text solr.StandardTokenizerFactory
tokenizer-query =
    text solr.StandardTokenizerFactory
    text solr.WhitespaceTokenizerFactory

[core2]
max-num-results = 99
unique-key = uniqueID
index =
    name:uniqueID type:uuid indexed:true stored:true default:NEW
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo bar type:text

additionalFieldConfig =
   <dynamicField name="*_public" type="string" indexed="true" stored="true"  multiValued="true"/>
   <dynamicField name="*_restricted" type="string" indexed="true" stored="true"  multiValued="true"/>

char-filter =
    text_ws solr.HTMLStripCharFilterFactory
char-filter-index =
    text_ws solr.MappingCharFilterFactory mapping="my-mapping.txt"
filter =
    text solr.ISOLatin1AccentFilterFactory
    text_ws Baz foo="bar" juca="bala"
filter-index =
    text solr.LowerCaseFilterFactory
filter-query =
    text solr.LowerCaseFilterFactory
    text solr.PorterStemFilterFactory
tokenizer-index =
    text solr.StandardTokenizerFactory
tokenizer-query =
    text solr.StandardTokenizerFactory
    text solr.WhitespaceTokenizerFactory
"""  # noqa


class SolrBaseTestCase(unittest.TestCase):
    globs = {}  # zc.buildout.testing needs this

    def setUp(self):
        buildoutSetUp(self)
        install_develop('Genshi', self)
        install_develop('collective.recipe.solrinstance', self)
        install_develop('hexagonit.recipe.download', self)
        install_develop('zope.exceptions', self)
        install_develop('zope.interface', self)
        install_develop('zope.testing', self)

    def tearDown(self):
        buildoutTearDown(self)

    def getpath(self, *args):
        return join(*([self.globs['sample_buildout']] + list(args)))

    def getfile(self, *args):
        filepath = self.getpath(*args)
        with open(filepath) as fh:
            return fh.read()

    def _test_field_types(self, schema_file):
        self.assertIn('analyzer type="index"', schema_file)
        self.assertIn('analyzer type="query"', schema_file)
        self.assertIn('<charFilter class="solr.HTMLStripCharFilterFactory',
                      schema_file)
        self.assertIn('<charFilter class="solr.MappingCharFilterFactory" '
                      'mapping="my-mapping.txt"', schema_file)
        self.assertIn('<tokenizer class="solr.WhitespaceTokenizerFactory',
                      schema_file)
        self.assertIn('<filter class="Baz"', schema_file)
        self.assertIn('<filter class="solr.PorterStemFilterFactory',
                      schema_file)
        self.assertIn('dynamicField name="*_public" ', schema_file)
        self.assertIn('dynamicField name="*_restricted" ', schema_file)

    def _basic_install(self, config):
        buildout = join(self.globs['sample_buildout'], 'buildout.cfg')
        with open(buildout, 'w') as fh:
            fh.write(config)
        buildout = self.globs['buildout']
        output = self.globs['system'](buildout)
        return output

    @contextmanager
    def use_core(self, *paths):
        core = {
            'name': paths[-1],
            'schema': self.getfile(*(paths + ('conf', 'schema.xml'))),
            'config': self.getfile(*(paths + ('conf', 'solrconfig.xml')))
        }

        yield core
