# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.base import BASE_CONF
from collective.recipe.solrinstance.tests.base import SolrBaseTestCase
from os.path import join
import os


class SolrSmokeTestCase(SolrBaseTestCase):

    def test_missing_solr_version(self):
        output = self._basic_install(BASE_CONF.format(addon=''))
        self.assertIn('Error: Missing option: solr:solr-version', output)

    def test_unsupported_solr1_install(self):
        config = BASE_CONF.format(addon='\nsolr-version = 1')
        output = self._basic_install(config)
        self.assertIn('Error: Solr 1.x is not supported.', output)

    def test_unsupported_solr2_install(self):
        config = BASE_CONF.format(addon='\nsolr-version = 2')
        output = self._basic_install(config)
        self.assertIn('Error: Solr 2.x is not supported.', output)

    def test_duplicate_core_definition_on_multicore_setup(self):
        sample = self.globs['sample_buildout']
        os.makedirs(join(sample, 'example', 'etc'))
        os.makedirs(join(sample, 'example', 'solr', 'conf'))
        os.makedirs(join(sample, 'dist'))
        os.makedirs(join(sample, 'contrib'))

        config = BASE_CONF.format(addon=""":mc
solr-version = 3
solr-location = {0}
cores =
    core1 core2
    core1
    core3""".format(self.globs['sample_buildout']))
        output = self._basic_install(config)
        self.assertIn('Error: Core \'core1\' was already defined.', output)
