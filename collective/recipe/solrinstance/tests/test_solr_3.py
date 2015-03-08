# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.base import MULTICORE_CONF
from collective.recipe.solrinstance.tests.base import SINGLE_CORE_CONF
from collective.recipe.solrinstance.tests.base import SolrBaseTestCase
import os
import shutil
import time


class Solr3TestCase(SolrBaseTestCase):

    version = 3

    def create_sample_download_directories(self):
        # Create Solr 3 download package directory structure
        sample = self.globs['sample_buildout']
        os.makedirs(os.path.join(sample, 'example', 'etc'))
        os.makedirs(os.path.join(sample, 'example', 'solr', 'conf'))
        os.makedirs(os.path.join(sample, 'dist'))
        os.makedirs(os.path.join(sample, 'contrib'))

    def _basic_singlecore_install(self):
        self.create_sample_download_directories()
        config = SINGLE_CORE_CONF.format(addon="""
solr-version={0}
solr-location={1}
""".format(self.version, self.globs['sample_buildout']))
        return self._basic_install(config)

    def _basic_multicore_install(self):
        self.create_sample_download_directories()
        config = MULTICORE_CONF.format(addon="""
solr-version={0}
solr-location={1}
""".format(self.version, self.globs['sample_buildout']))

        return self._basic_install(config)

    def test_artifact_prefix(self):
        self._basic_singlecore_install()

        with self.use_core('parts', 'solr', 'solr') as c:
            self.assertIn('apache-', c['config'])

    def test_singlecore_install(self):
        out = self._basic_singlecore_install()
        aI = self.assertIn
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
            aI('<dataDir>{0:s}/var/solr/data</dataDir>'.format(
                self.globs['sample_buildout']), c['config'])

    def test_multicore_install(self):
        out = self._basic_multicore_install()
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

        # ... and it's config files
        for core in ('core1', 'core2'):
            aI('{0:s}: Generated file \'solrconfig.xml\'.'.format(core), out)
            aI('{0:s}: Generated file \'schema.xml\'.'.format(core), out)
            aI('{0:s}: Generated file \'stopwords.txt\'.'.format(core), out)

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
                self.globs['sample_buildout'], c['name']), c['config'])

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
                self.globs['sample_buildout'], c['name']), c['config'])

    def test_core_configuration_on_multicore_install(self):
        out = self._basic_multicore_install()

        # ... but solr.xml with core setup
        aI = self.assertIn
        aI('solr-mc: Generated file \'solr.xml\'.', out)

        core_conf = self.getfile('parts', 'solr-mc', 'solr', 'solr.xml')
        for core in ('core1', 'core2'):
            aI('<core name="{0:s}" instanceDir="{0:s}" />'.format(core),
               core_conf)

    def test_install_is_not_called_on_update_if_instance_exists(self):
        # we test this on multicore setups, because they're setup are
        # equal among all supported solr versions.
        self._basic_multicore_install()
        conf = self.getpath(
            'parts', 'solr-mc', 'solr', 'core1', 'conf', 'solrconfig.xml')
        ctime = os.stat(conf).st_ctime
        time.sleep(1)
        self.globs['system'](self.globs['buildout'])
        self.assertEqual(os.stat(conf).st_ctime, ctime)

    def test_install_is_called_on_update_if_instance_not_exists(self):
        # we test this on multicore setups, because they're setup are
        # equal among all supported solr versions.
        self._basic_multicore_install()
        conf = self.getpath(
            'parts', 'solr-mc', 'solr', 'core1', 'conf', 'solrconfig.xml')
        ctime = os.stat(conf).st_ctime
        shutil.rmtree(self.getpath('parts', 'solr-mc'))
        time.sleep(1)
        self.globs['system'](self.globs['buildout'])
        self.assertNotEqual(os.stat(conf).st_ctime, ctime)
