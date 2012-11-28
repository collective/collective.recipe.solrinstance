import unittest
import os
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
java_opts =
    -Xms512M
    -Xmx1024M

[core1]
max-num-results = 55
unique-key = uniqueID
index =
    name:uniqueID type:uuid indexed:true stored:true default:NEW
    # You can add comment lines among index definitions
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo bar type:text
    name:BlaWS type:text_ws
filter =
    text solr.ISOLatin1AccentFilterFactory
    text_ws Baz foo="bar" juca="bala"

[core2]
max-num-results = 99
unique-key = uniqueID
index =
    name:uniqueID type:uuid indexed:true stored:true default:NEW
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo bar type:text
filter =
    text solr.ISOLatin1AccentFilterFactory
    text_ws Baz foo="bar" juca="bala"
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
filter =
    text solr.ISOLatin1AccentFilterFactory
    text_ws Baz foo="bar" juca="bala"
"""


class TestSolr4(unittest.TestCase):
    globs = {}  # zc.buildout.testing needs this

    def setUp(self):
        buildoutSetUp(self)
        install_develop('zope.exceptions', self)
        install_develop('zope.interface', self)
        install_develop('zope.testing', self)
        install_develop('Cheetah', self)
        install_develop('Markdown', self)
        install_develop('iw.recipe.template', self)
        install_develop('collective.recipe.solrinstance', self)
        sample_buildout = self.globs['sample_buildout']
        os.makedirs(join(sample_buildout, 'example', 'etc'))
        os.makedirs(join(
            sample_buildout, 'example', 'solr', 'collection1', 'conf'))
        os.makedirs(join(sample_buildout, 'dist'))
        os.makedirs(join(sample_buildout, 'contrib'))

    def tearDown(self):
        buildoutTearDown(self)

    def getfile(self, *args):
        filepath = os.path.join(*(
            [self.globs['sample_buildout']] + list(args)
        ))
        with open(filepath) as fh:
            return fh.read()

    def test_basic_install(self):
        with open(join(self.globs['sample_buildout'], 'buildout.cfg'), 'w') as fh:
            fh.write(SINGLE_CORE_CONF)
        sample_buildout = self.globs['sample_buildout']
        buildout = self.globs['buildout']
        install_output = dedent("""
            Installing solr.
            jetty.xml: Generated file 'jetty.xml'.
            logging.properties: Generated file 'logging.properties'.
            solrconfig.xml: Generated file 'solrconfig.xml'.
            schema.xml: Generated file 'schema.xml'.
            stopwords.txt: Generated file 'stopwords.txt'.
            solr-instance: Generated script 'solr-instance'
        """).strip()
        output = self.globs['system'](buildout)
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

        solrconfig_file = self.getfile(
            'parts', 'solr', 'solr', 'collection1', 'conf', 'solrconfig.xml')
        datadir = "<dataDir>%s/var/solr/data</dataDir>" % sample_buildout
        self.assertTrue(datadir in solrconfig_file)
        self.assertTrue('<int name="rows">99</int>' in solrconfig_file)

    def test_multicore(self):
        with open(join(self.globs['sample_buildout'], 'buildout.cfg'), 'w') as fh:
            fh.write(MULTICORE_CONF)
        install_output = dedent("""
            Installing solr-mc.
            solr.xml: Generated file 'solr.xml'.
            solrconfig.xml: Generated file 'solrconfig.xml'.
            stopwords.txt: Generated file 'stopwords.txt'.
            schema.xml: Generated file 'schema.xml'.
            solrconfig.xml: Generated file 'solrconfig.xml'.
            stopwords.txt: Generated file 'stopwords.txt'.
            schema.xml: Generated file 'schema.xml'.
            jetty.xml: Generated file 'jetty.xml'.
            logging.properties: Generated file 'logging.properties'.
            solr-instance: Generated script 'solr-instance'.
        """).strip()
        output = self.globs['system'](self.globs['buildout'])
        self.assertTrue(install_output in output, output)
        solr_xml = self.getfile('parts', 'solr-mc', 'solr', 'solr.xml')
        self.assertTrue('<core name="core1" instanceDir="core1" />' in solr_xml)
        self.assertTrue('<core name="core2" instanceDir="core2" />' in solr_xml)
        core1_schema = self.getfile('parts', 'solr-mc', 'solr', 'core1', 'conf', 'schema.xml')
        self.assertTrue('<schema name="core1"' in core1_schema)
        self.assertTrue('<field name="BlaWS" type="text_ws" indexed="true"' in core1_schema)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSolr4))
    return suite
