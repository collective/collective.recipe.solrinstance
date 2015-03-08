# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.test_solr_3 import Solr3TestCase
import os


class Solr4xTestCase(Solr3TestCase):

    version = 4

    def create_sample_download_directories(self):
        # Create Solr 4 download package directory structure
        join = os.path.join
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'collection1', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

    def test_artifact_prefix(self):
        self._basic_singlecore_install()
        with self.use_core('parts', 'solr', 'solr', 'collection1') as c:
            self.assertNotIn('apache-', c['config'])

    def test_singlecore_install(self):
        out = self._basic_singlecore_install()
        aI = self.assertIn
        aI('Installing solr.', out)
        aI('solr: Generated file \'jetty.xml\'.', out)
        aI('solr: Generated file \'log4j.properties\'.', out)
        aI('solr: Generated file \'logging.properties\'.', out)
        aI('solr: Generated script \'solr-instance\'.', out)
        aI('solr: Generated file \'solr.xml\'.', out)
        aI('collection1: Generated file \'schema.xml\'.', out)
        aI('collection1: Generated file \'stopwords.txt\'.', out)
        aI('collection1: Generated file \'solrconfig.xml\'.', out)

        # Script
        solr_instance_script = self.getfile('bin', 'solr-instance')
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        # Jetty
        jetty_file = self.getfile('parts', 'solr', 'etc', 'jetty.xml')
        self.assertTrue('<Set name="port">1234</Set>' in jetty_file)

        # Schema
        with self.use_core('parts', 'solr', 'solr', 'collection1') as c:
            aI('<field name="Foo" type="text" indexed="true"', c['schema'])
            aI('<field name="Bar" type="date" indexed="false"', c['schema'])
            aI('<field name="Foo bar" type="text" indexed="true"', c['schema'])
            aI('<uniqueKey>uniqueID</uniqueKey>', c['schema'])
            self._test_field_types(c['schema'])

            aI('<int name="rows">99</int>', c['config'])
            aI('<dataDir>{0:s}/var/solr/data/collection1</dataDir>'.format(
                self.globs['sample_buildout']), c['config'])

            self.assertIn('class="${solr.directoryFactory:solr.'
                          'NRTCachingDirectoryFactory}', c['config'])

    def test_multicore_install(self):
        super(Solr4xTestCase, self).test_multicore_install()

        with self.use_core('parts', 'solr-mc', 'solr', 'core1') as c:
            self.assertIn('class="${solr.directoryFactory:solr.'
                          'StandardDirectoryFactory}', c['config'])
        with self.use_core('parts', 'solr-mc', 'solr', 'core2') as c:
            self.assertIn('class="${solr.directoryFactory:solr.'
                          'RAMDirectoryFactory}', c['config'])


class Solr40TestCase(Solr4xTestCase):
    """ Test for Solr 4.0 - artifacts were prefixed with ``apache-``.
    """

    def create_sample_download_directories(self):
        super(Solr40TestCase, self).create_sample_download_directories()
        sample_buildout = self.globs['sample_buildout']
        os.makedirs(
            os.path.join(sample_buildout, 'dist', 'apache-solr-4.0.war'))

    def test_artifact_prefix(self):
        self._basic_singlecore_install()

        # The `apache-` library prefix was removed in Solr 4.1.0,
        # see changelog here: http://bit.ly/1DVBqRC
        with self.use_core('parts', 'solr', 'solr', 'collection1') as c:
            self.assertIn('apache-', c['config'])
