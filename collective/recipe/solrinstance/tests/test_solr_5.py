# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.test_solr_4 import Solr4xTestCase
import os
import shutil
import time


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

    def test_single_directory_factory_default(self):
        self._basic_singlecore_install()
        with self.use_core('parts', 'solr', 'solr') as c:
            self.assertIn('class="${solr.directoryFactory:solr.'
                          'NRTCachingDirectoryFactory}', c['config'])

    def test_install_is_not_called_on_update_if_instance_exists(self):
        self._basic_singlecore_install()
        solrconfig_file = self.getpath(
            'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
        ctime = os.stat(solrconfig_file).st_ctime

        time.sleep(1)
        buildout = self.globs['buildout']
        self.globs['system'](buildout)
        self.assertEqual(os.stat(solrconfig_file).st_ctime, ctime)

    def test_install_is_called_on_update_if_instance_not_exists(self):
        self._basic_singlecore_install()
        solrconfig_file = self.getpath(
            'parts', 'solr', 'solr', 'conf', 'solrconfig.xml')
        ctime = os.stat(solrconfig_file).st_ctime
        shutil.rmtree(self.getpath('parts', 'solr'))

        time.sleep(1)
        buildout = self.globs['buildout']
        self.globs['system'](buildout)
        self.assertNotEqual(os.stat(solrconfig_file).st_ctime, ctime)

    def test_core_configuration_on_multicore_install(self):
        out = self._basic_multicore_install()

        # ... but solr.xml with core setup
        self.assertIn('solr-mc: Generated file \'solr.xml\'.', out)

        for core in ('core1', 'core2'):
            core_properties = self.getfile(
                'parts', 'solr-mc', 'solr', core, 'core.properties')
            self.assertIn(core, core_properties)
