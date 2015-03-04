# -*- coding: utf-8 -*-
from os.path import join
from zc.buildout.testing import buildoutSetUp, buildoutTearDown
from zc.buildout.testing import install_develop
import os
import unittest

BASE_CONF = """\
[buildout]
parts = solr

[solr]
recipe = collective.recipe.solrinstance{addon:s}
"""

SINGLE_CORE_CONF = """
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
    # Support names with spaces
    name:Foo bar type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true

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


class RecipeTestCase(unittest.TestCase):
    globs = {}  # zc.buildout.testing needs this

    def setUp(self):
        buildoutSetUp(self)
        install_develop('zope.exceptions', self)
        install_develop('zope.interface', self)
        install_develop('zope.testing', self)
        install_develop('Genshi', self)
        install_develop('hexagonit.recipe.download', self)
        install_develop('collective.recipe.solrinstance', self)

    def tearDown(self):
        buildoutTearDown(self)

    def getpath(self, *args):
        filepath = os.path.join(*(
            [self.globs['sample_buildout']] + list(args)
        ))
        return filepath

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

    def test_missing_solr_version(self):
        output = self._basic_install(BASE_CONF.format(addon=''))
        self.assertIn('Error: Missing option: solr:solr-version', output)

    def test_unsupported_solr1_install(self):
        config = BASE_CONF.format(addon='\nsolr-version=1')
        output = self._basic_install(config)
        self.assertIn('Error: Solr 1.x is not supported.', output)

    def test_unsupported_solr2_install(self):
        config = BASE_CONF.format(addon='\nsolr-version=2')
        output = self._basic_install(config)
        self.assertIn('Error: Solr 2.x is not supported.', output)

    def test_solr3_install_invalid_config_missing_uid_index(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = BASE_CONF.format(addon="""
solr-version=3
solr-location={0:s}
unique-key = uid
index =
    name:uniqueID type:string indexed:true stored:true required:true
""".format(sample))

        output = self._basic_install(config)
        self.assertIn('Installing solr.', output)
        self.assertIn('Error: Unique key without matching index: uid', output)

    def test_solr3_install_invalid_config_duplicate_fields(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = BASE_CONF.format(addon="""
solr-version=3
solr-location={0:s}
unique-key = uniqueID
index =
    name:uniqueID type:string indexed:true stored:true required:true
    # You can add comment lines among index definitions
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo type:text
""".format(sample))  # noqa

        output = self._basic_install(config)
        self.assertIn('Installing solr.', output)
        self.assertIn(
            'Error: Duplicate name error: "Foo" already defined.', output)

    def test_solr3_install(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = SINGLE_CORE_CONF.format(addon="""
solr-version=3
solr-location={0:s}
""".format(sample))

        output = self._basic_install(config)
        self.assertIn('Installing solr.', output)
        self.assertIn('solr: Generated file \'jetty.xml\'.', output)
        self.assertIn('solr: Generated file \'log4j.properties\'.', output)
        self.assertIn('solr: Generated file \'logging.properties\'.', output)
        self.assertIn('solr: Generated script \'solr-instance\'.', output)
        self.assertIn('solr: Generated file \'solrconfig.xml\'.', output)
        self.assertIn('solr: Generated file \'schema.xml\'.', output)
        self.assertIn('solr: Generated file \'stopwords.txt\'.', output)

        # Script
        solr_instance_script = self.getfile('bin', 'solr-instance')
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        # Jetty
        jetty_file = self.getfile('parts', 'solr', 'etc', 'jetty.xml')
        self.assertTrue('<Set name="port">1234</Set>' in jetty_file)

        # Schema
        schema_file = self.getfile(
            'parts', 'solr', 'solr', 'conf', 'schema.xml')
        self.assertIn('<field name="Foo" type="text" indexed="true"',
                      schema_file)
        self.assertIn('<field name="Bar" type="date" indexed="false"',
                      schema_file)
        self.assertIn('<field name="Foo bar" type="text" indexed="true"',
                      schema_file)
        self.assertIn('<uniqueKey>uniqueID</uniqueKey>', schema_file)
        self._test_field_types(schema_file)

        # Config
        solrconfig_file = self.getfile(
            'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
        self.assertIn('<int name="rows">99</int>', solrconfig_file)

        self.assertIn('<dataDir>{0:s}/var/solr/data</dataDir>'.format(sample),
                      solrconfig_file)

    # TODO: Add more tests for solr4 and solr5
