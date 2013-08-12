import os
import shutil
import time
import unittest
from textwrap import dedent
from os.path import join
from zc.buildout.testing import buildoutSetUp, buildoutTearDown
from zc.buildout.testing import install_develop

MULTICORE_CONF = """
[buildout]
parts = solr-mc

[solr-mc]
recipe = collective.recipe.solrinstance:mc
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
"""

SINGLE_CORE_CONF = """
[buildout]
parts = solr

[solr]
recipe = collective.recipe.solrinstance
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
"""


class TestSolr4(unittest.TestCase):
    globs = {}  # zc.buildout.testing needs this

    def setUp(self):
        buildoutSetUp(self)
        install_develop('zope.exceptions', self)
        install_develop('zope.interface', self)
        install_develop('zope.testing', self)
        install_develop('Genshi', self)
        install_develop('collective.recipe.solrinstance', self)
        sample_buildout = self.globs['sample_buildout']
        os.makedirs(join(sample_buildout, 'example', 'etc'))
        os.makedirs(join(
            sample_buildout, 'example', 'solr', 'collection1', 'conf'))
        os.makedirs(join(sample_buildout, 'dist'))
        os.makedirs(join(sample_buildout, 'contrib'))

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
        self.assertTrue('analyzer type="index"' in schema_file)
        self.assertTrue('analyzer type="query"' in schema_file)
        self.assertTrue('<charFilter class="solr.HTMLStripCharFilterFactory' \
                        in schema_file)
        self.assertTrue('<charFilter class="solr.MappingCharFilterFactory" mapping="my-mapping.txt"' in schema_file)
        self.assertTrue('<tokenizer class="solr.WhitespaceTokenizerFactory' \
                        in schema_file)
        self.assertTrue('<filter class="Baz"' in schema_file)
        self.assertTrue('<filter class="solr.PorterStemFilterFactory' \
                        in schema_file)

        self.assertTrue('dynamicField name="*_public" ' in schema_file)
        self.assertTrue('dynamicField name="*_restricted" ' in schema_file)

    def _basic_install(self):
        with open(join(self.globs['sample_buildout'], 'buildout.cfg'), 'w') as fh:
            fh.write(SINGLE_CORE_CONF)
        buildout = self.globs['buildout']
        output = self.globs['system'](buildout)
        return output

    def _multicore_install(self):
        with open(join(self.globs['sample_buildout'], 'buildout.cfg'), 'w') as fh:
            fh.write(MULTICORE_CONF)
        output = self.globs['system'](self.globs['buildout'])
        return output

    def test_basic_install(self):
        output = self._basic_install()
        sample_buildout = self.globs['sample_buildout']
        install_output = dedent("""
            Installing solr.
            solr: Generated file 'jetty.xml'.
            solr: Generated file 'log4j.properties'.
            solr: Generated file 'logging.properties'.
            solr: Generated file 'solrconfig.xml'.
            solr: Generated file 'schema.xml'.
            solr: Generated file 'stopwords.txt'.
            solr: Generated script 'solr-instance'
        """).strip()

        self.assertTrue(install_output in output, output)

        solr_instance_script = self.getfile('bin', 'solr-instance')
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        jetty_file = self.getfile('parts', 'solr', 'etc', 'jetty.xml')
        self.assertTrue('<Set name="port">1234</Set>' in jetty_file)
        schema_file = self.getfile(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'schema.xml')
        foo = '<field name="Foo" type="text" indexed="true"'
        self.assertTrue(foo in schema_file)
        bar = '<field name="Bar" type="date" indexed="false"'
        self.assertTrue(bar in schema_file)
        foobar = 'name="Foo bar" type="text" indexed="true"'
        self.assertTrue(foobar in schema_file)
        self.assertTrue('<uniqueKey>uniqueID</uniqueKey>' in schema_file)

        self._test_field_types(schema_file)

        solrconfig_file = self.getfile(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        datadir = "<dataDir>%s/var/solr/data</dataDir>" % sample_buildout
        self.assertTrue(datadir in solrconfig_file)
        self.assertTrue('<int name="rows">99</int>' in solrconfig_file)

    def test_single_directory_factory_default(self):
        self._basic_install()
        solrconfig_file = self.getfile(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        self.assertTrue(
            'class="${solr.directoryFactory:solr.NRTCachingDirectoryFactory}'
            in solrconfig_file)

    def test_artifact_prefix(self):
        self._basic_install()
        solrconfig_file = self.getfile(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        self.assertTrue('apache-' not in solrconfig_file)

    def test_multicore(self):
        install_output = dedent("""
            Installing solr-mc.
            solr-mc: Generated file 'solr.xml'.
            solr-mc: Generated file 'solrconfig.xml'.
            solr-mc: Generated file 'stopwords.txt'.
            solr-mc: Generated file 'schema.xml'.
            solr-mc: Generated file 'solrconfig.xml'.
            solr-mc: Generated file 'stopwords.txt'.
            solr-mc: Generated file 'schema.xml'.
            solr-mc: Generated file 'jetty.xml'.
            solr-mc: Generated file 'log4j.properties'.
            solr-mc: Generated file 'logging.properties'.
            solr-mc: Generated script 'solr-instance'.
        """).strip()
        output = self._multicore_install()
        self.assertTrue(install_output in output, output)
        solr_xml = self.getfile('parts', 'solr-mc', 'solr', 'solr.xml')
        self.assertTrue('<core name="core1" instanceDir="core1" />' in solr_xml)
        self.assertTrue('<core name="core2" instanceDir="core2" />' in solr_xml)
        core1_schema = self.getfile('parts', 'solr-mc', 'solr', 'core1', 'conf', 'schema.xml')
        self.assertTrue('<schema name="core1"' in core1_schema)
        self.assertTrue('<field name="BlaWS" type="text_ws" indexed="true"' in core1_schema)
        self._test_field_types(core1_schema)

    def test_multicore_directory_factory(self):
        self._multicore_install()
        core1_config = self.getfile(
            'parts', 'solr-mc', 'solr', 'core1', 'conf', 'solrconfig.xml')

        core2_config = self.getfile(
            'parts', 'solr-mc', 'solr', 'core2', 'conf', 'solrconfig.xml')

        self.assertTrue(
            'class="${solr.directoryFactory:solr.StandardDirectoryFactory}' in
            core1_config)

        self.assertTrue(
            'class="${solr.directoryFactory:solr.RAMDirectoryFactory}' in
            core2_config)

    def test_install_is_not_called_on_update_if_instance_exists(self):
        self._basic_install()
        solrconfig_file = self.getpath(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        ctime = os.stat(solrconfig_file).st_ctime

        time.sleep(1)
        buildout = self.globs['buildout']
        self.globs['system'](buildout)
        self.assertEqual(os.stat(solrconfig_file).st_ctime, ctime)

    def test_install_is_called_on_update_if_not_instance_exists(self):
        self._basic_install()
        solrconfig_file = self.getpath(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        ctime = os.stat(solrconfig_file).st_ctime
        shutil.rmtree(self.getpath('parts', 'solr'))

        time.sleep(1)
        buildout = self.globs['buildout']
        self.globs['system'](buildout)
        self.assertNotEqual(os.stat(solrconfig_file).st_ctime, ctime)


class TestSolr40(TestSolr4):
    """ Test for Solr 4.0 - artifacts were prefixed with ``apache-``.
    """
    def setUp(self):
        super(TestSolr40, self).setUp()
        sample_buildout = self.globs['sample_buildout']
        os.makedirs(join(sample_buildout, 'dist', 'apache-solr-4.0.war'))

    def test_artifact_prefix(self):
        self._basic_install()
        solrconfig_file = self.getfile(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        self.assertTrue('apache-' in solrconfig_file)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSolr4))
    suite.addTest(unittest.makeSuite(TestSolr40))
    return suite
