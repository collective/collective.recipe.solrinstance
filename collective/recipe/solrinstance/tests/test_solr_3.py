# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.base import BASE_CONF
from collective.recipe.solrinstance.tests.base import MULTICORE_CONF
from collective.recipe.solrinstance.tests.base import SINGLE_CORE_CONF
from collective.recipe.solrinstance.tests.base import SolrBaseTestCase
from os.path import join
import os


class Solr3TestCase(SolrBaseTestCase):

    version = 3

    def test_solr_install_invalid_config_missing_uid_index(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = BASE_CONF.format(addon="""
solr-version={0}
solr-location={1}
unique-key = uid
index =
    name:uniqueID type:string indexed:true stored:true required:true
""".format(self.version, sample))

        aI = self.assertIn
        out = self._basic_install(config)
        aI('Installing solr.', out)
        aI('Error: Unique key without matching index: uid', out)

    def test_solr_install_invalid_config_duplicate_fields(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = BASE_CONF.format(addon="""
solr-version={0}
solr-location={1}
unique-key = uniqueID
index =
    name:uniqueID type:string indexed:true stored:true required:true
    # You can add comment lines among index definitions
    name:Foo type:text
    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
    name:Foo type:text
""".format(self.version, sample))  # noqa

        out = self._basic_install(config)

        aI = self.assertIn
        aI('Installing solr.', out)
        aI('Error: Duplicate name error: "Foo" already defined.', out)

    def test_singlecore_install(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = SINGLE_CORE_CONF.format(addon="""
solr-version={0}
solr-location={1}
""".format(self.version, sample))

        aI = self.assertIn
        out = self._basic_install(config)
        aI('Installing solr.', out)
        aI('solr: Generated file \'jetty.xml\'.', out)
        aI('solr: Generated file \'log4j.properties\'.', out)
        aI('solr: Generated file \'logging.properties\'.', out)
        aI('solr: Generated script \'solr-instance\'.', out)
        aI('solr: Generated file \'schema.xml\'.', out)
        aI('solr: Generated file \'stopwords.txt\'.', out)

        # No solr.xml should be generated, but solrconfig.xml
        self.assertNotIn('solr: Generated file \'solr.xml\'.', out)
        aI('solr: Generated file \'solrconfig.xml\'.', out)

        # Script
        solr_instance_script = self.getfile('bin', 'solr-instance')
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        # Jetty
        jetty_file = self.getfile('parts', 'solr', 'etc', 'jetty.xml')
        self.assertTrue('<Set name="port">1234</Set>' in jetty_file)

        # Schema
        with self.use_core('parts', 'solr', 'solr') as c:
            aI('<field name="Foo" type="text" indexed="true"', c['schema'])
            aI('<field name="Bar" type="date" indexed="false"', c['schema'])
            aI('<field name="Foo bar" type="text" indexed="true"', c['schema'])
            aI('<uniqueKey>uniqueID</uniqueKey>', c['schema'])
            self._test_field_types(c['schema'])

            aI('<int name="rows">99</int>', c['config'])
            aI('<dataDir>{0:s}/var/solr/data</dataDir>'.format(sample),
               c['config'])

    def test_multicore_install(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = MULTICORE_CONF.format(addon="""
solr-version={0}
solr-location={1}
""".format(self.version, sample))

        out = self._basic_install(config)

        aI = self.assertIn
        aI('Installing solr-mc.', out)
        aI('solr-mc: Generated file \'jetty.xml\'.', out)
        aI('solr-mc: Generated file \'log4j.properties\'.', out)
        aI('solr-mc: Generated file \'logging.properties\'.', out)
        aI('solr-mc: Generated script \'solr-instance\'.', out)

        # No solrconfig.xml, schema.xml and stopwords.txt should be generated
        self.assertNotIn('solr-mc: Generated file \'solrconfig.xml\'.', out)
        self.assertNotIn('solr-mc: Generated file \'schema.xml\'.', out)
        self.assertNotIn('solr-mc: Generated file \'stopwords.txt\'.', out)

        # ... but solr.xml with core setup
        aI('solr-mc: Generated file \'solr.xml\'.', out)

        # ... and for each core an entry in solr.xml and it's config files
        core_conf = self.getfile('parts', 'solr-mc', 'solr', 'solr.xml')
        for core in ('core1', 'core2'):
            aI('{0:s}: Generated file \'solrconfig.xml\'.'.format(core), out)
            aI('{0:s}: Generated file \'schema.xml\'.'.format(core), out)
            aI('{0:s}: Generated file \'stopwords.txt\'.'.format(core), out)

            # solr.xml
            aI('<core name="{0:s}" instanceDir="{0:s}" />'.format(core),
               core_conf)

        # Jetty
        jetty_file = self.getfile('parts', 'solr-mc', 'etc', 'jetty.xml')
        self.assertTrue('<Set name="port">1234</Set>' in jetty_file)

        # Script
        solr_instance_script = self.getfile('bin', 'solr-instance')
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        # Core 1
        with self.use_core('parts', 'solr-mc', 'solr', 'core1') as c:

            aI('<field name="Foo" type="text" indexed="true"', c['schema'])
            aI('<field name="Bar" type="date" indexed="false"', c['schema'])
            aI('<field name="Foo bar" type="text" indexed="true"', c['schema'])
            aI('<field name="BlaWS" type="text_ws" indexed="true"',
               c['schema'])

            aI('<uniqueKey>uniqueID</uniqueKey>', c['schema'])
            self._test_field_types(c['schema'])

            aI('<int name="rows">55</int>', c['config'])
            aI('<dataDir>{0:s}/var/solr/data/{1:s}</dataDir>'.format(
                sample, c['name']), c['config'])

        with self.use_core('parts', 'solr-mc', 'solr', 'core2') as c:

            aI('<field name="Foo" type="text" indexed="true"', c['schema'])
            aI('<field name="Bar" type="date" indexed="false"', c['schema'])
            aI('<field name="Foo bar" type="text" indexed="true"', c['schema'])
            self.assertNotIn(
                '<field name="BlaWS" type="text_ws" indexed="true"',
                c['schema']
            )

            aI('<uniqueKey>uniqueID</uniqueKey>', c['schema'])
            self._test_field_types(c['schema'])

            aI('<int name="rows">99</int>', c['config'])
            aI('<dataDir>{0:s}/var/solr/data/{1:s}</dataDir>'.format(
                sample, c['name']), c['config'])
