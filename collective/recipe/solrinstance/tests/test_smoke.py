# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.base import BASE_CONF
from collective.recipe.solrinstance.tests.base import SolrBaseTestCase
import os


class SolrSmokeTestCase(SolrBaseTestCase):

    def create_sample_download_directories(self):
        # Create Solr 3 download package directory structure
        sample = self.globs['sample_buildout']
        os.makedirs(os.path.join(sample, 'example', 'etc'))
        os.makedirs(os.path.join(sample, 'example', 'solr', 'conf'))
        os.makedirs(os.path.join(sample, 'dist'))
        os.makedirs(os.path.join(sample, 'contrib'))

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
        self.create_sample_download_directories()
        config = BASE_CONF.format(addon=""":mc
solr-version = 3
solr-location = {0}
cores =
    core1 core2
    core1
    core3""".format(self.globs['sample_buildout']))
        output = self._basic_install(config)

        aI = self.assertIn
        aI('Installing solr.', output)
        aI('Error: Core \'core1\' was already defined.', output)

    def test_solr_install_invalid_config_missing_uid_index(self):
        self.create_sample_download_directories()
        config = BASE_CONF.format(addon="""
solr-version = 3
solr-location = {0}
unique-key = uid
index =
    name:uniqueID type:string indexed:true stored:true required:true
""".format(self.globs['sample_buildout']))

        output = self._basic_install(config)

        aI = self.assertIn
        aI('Installing solr.', output)
        aI('Error: Unique key without matching index: uid', output)

    def test_solr_install_invalid_config_duplicate_fields(self):
        self.create_sample_download_directories()
        config = BASE_CONF.format(addon="""
solr-version = 3
solr-location = {0}
unique-key = uniqueID
index =
    name:uniqueID type:string indexed:true stored:true required:true
    # You can add comment lines among index definitions
    name:Foo type:text
    name:Bar type:date
    name:Foo type:text
""".format(self.globs['sample_buildout']))

        output = self._basic_install(config)

        aI = self.assertIn
        aI('Installing solr.', output)
        aI('Error: Duplicate name error: "Foo" already defined.', output)

    def test_solr_install_invalid_num_results(self):
        self.create_sample_download_directories()
        config = BASE_CONF.format(addon="""
solr-version = 3
solr-location = {0}
unique-key = uniqueID
max-num-results = -1
index =
    name:uniqueID type:string indexed:true stored:true required:true
""".format(self.globs['sample_buildout']))

        output = self._basic_install(config)

        aI = self.assertIn
        aI('Error: Please use a positive integer as max-num-results.', output)

    def test_solr_install_invalid_default_operator(self):
        self.create_sample_download_directories()
        config = BASE_CONF.format(addon="""
solr-version = 3
solr-location = {0}
unique-key = uniqueID
default-operator = and
index =
    name:uniqueID type:string indexed:true stored:true required:true
""".format(self.globs['sample_buildout']))

        output = self._basic_install(config)

        aI = self.assertIn
        aI('Error: Only one of (\'OR\', \'AND\') allowed as '
           'default-operator.', output)
