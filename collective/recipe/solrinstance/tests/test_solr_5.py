# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.test_solr_4 import Solr4xTestCase
import os


class Solr5TestCase(Solr4xTestCase):

    version = 5

    def create_sample_download_directories(self):
        # Create Solr 5 download package directory structure
        sample = self.globs['sample_buildout']
        os.makedirs(os.path.join(sample, 'dist'))
        os.makedirs(os.path.join(sample, 'contrib'))
        os.makedirs(os.path.join(sample, 'server', 'etc'))
        os.makedirs(os.path.join(
            sample, 'server', 'solr', 'configsets', 'basic_configs', 'conf'))
        os.makedirs(os.path.join(
            sample, 'server', 'solr', 'configsets',
            'data_driven_schema_configs', 'conf'))
        os.makedirs(os.path.join(
            sample, 'server', 'solr', 'configsets',
            'sample_techproducts_configs', 'conf'))

    def test_artifact_prefix(self):
        self._basic_multicore_install()
        with self.use_core('parts', 'solr-mc', 'solr', 'core1') as c:
            self.assertNotIn('apache-', c['config'])

    def test_singlecore_install(self):
        output = self._basic_singlecore_install()
        self.assertIn('Error: Solr 5 no longer supports deprecated single '
                      'core setups. Please use a multicore setup with one '
                      'core.', output)

    def test_core_configuration_on_multicore_install(self):
        out = self._basic_multicore_install()

        # ... but solr.xml with core setup
        self.assertIn('solr-mc: Generated file \'solr.xml\'.', out)

        for core in ('core1', 'core2'):
            core_properties = self.getfile(
                'parts', 'solr-mc', 'solr', core, 'core.properties')
            self.assertIn(core, core_properties)
