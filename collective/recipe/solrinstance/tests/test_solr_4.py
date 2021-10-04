# -*- coding: utf-8 -*-
from collective.recipe.solrinstance.tests.base import MULTICORE_CONF
from collective.recipe.solrinstance.tests.base import SINGLE_CORE_CONF
from collective.recipe.solrinstance.tests.base import SolrBaseTestCase

import os
import shutil
import time


class Solr4xTestCase(SolrBaseTestCase):

    version = 4

    def create_sample_download_directories(self):
        # Create Solr 4 download package directory structure
        join = os.path.join
        sample = self.globs["sample_buildout"]
        os.makedirs(join(sample, "example", "etc"))
        os.makedirs(join(sample, "example", "solr", "collection1", "conf"))
        os.makedirs(join(sample, "dist"))
        os.makedirs(join(sample, "contrib"))

    def _basic_singlecore_install(self):
        self.create_sample_download_directories()
        config = SINGLE_CORE_CONF.format(
            addon="""
solr-version={0}
solr-location={1}
""".format(
                self.version, self.globs["sample_buildout"]
            )
        )
        return self._basic_install(config)

    def _basic_multicore_install(self):
        self.create_sample_download_directories()
        config = MULTICORE_CONF.format(
            addon="""
solr-version={0}
solr-location={1}
""".format(
                self.version, self.globs["sample_buildout"]
            )
        )

        return self._basic_install(config)

    def test_artifact_prefix(self):
        self._basic_singlecore_install()
        with self.use_core("parts", "solr", "solr", "collection1") as c:
            self.assertNotIn("apache-", c["config"])

    def test_singlecore_install(self):
        out = self._basic_singlecore_install()
        aI = self.assertIn
        aI("Installing solr.", out)
        aI("solr: Generated file 'jetty.xml'.", out)
        aI("solr: Generated file 'log4j.properties'.", out)
        aI("solr: Generated file 'logging.properties'.", out)
        aI("solr: Generated script 'solr-instance'.", out)
        aI("solr: Generated file 'solr.xml'.", out)
        aI("collection1: Generated file 'schema.xml'.", out)
        aI("collection1: Generated file 'stopwords.txt'.", out)
        aI("collection1: Generated file 'solrconfig.xml'.", out)

        # Script
        solr_instance_script = self.getfile("bin", "solr-instance")
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        # Jetty
        jetty_file = self.getfile("parts", "solr", "etc", "jetty.xml")
        self.assertTrue(
            '<Set name="port"><SystemProperty name="jetty.port"'
            ' default="1234" /></Set>' in jetty_file
        )

        # Schema
        with self.use_core("parts", "solr", "solr", "collection1") as c:
            aI('<field name="Foo" type="text" indexed="true"', c["schema"])
            aI('<field name="Bar" type="date" indexed="false"', c["schema"])
            aI('<field name="Foo bar" type="text" indexed="true"', c["schema"])
            aI("<uniqueKey>uniqueID</uniqueKey>", c["schema"])
            self._test_field_types(c["schema"])

            aI('<int name="rows">99</int>', c["config"])
            aI(
                "<dataDir>{0:s}/var/solr/data/collection1</dataDir>".format(
                    self.globs["sample_buildout"]
                ),
                c["config"],
            )

            self.assertIn(
                'class="${solr.directoryFactory:solr.' "NRTCachingDirectoryFactory}",
                c["config"],
            )

    def test_multicore_install(self):
        out = self._basic_multicore_install()
        aI = self.assertIn
        aI("Installing solr-mc.", out)
        aI("solr-mc: Generated file 'jetty.xml'.", out)
        aI("solr-mc: Generated file 'log4j.properties'.", out)
        aI("solr-mc: Generated file 'logging.properties'.", out)
        aI("solr-mc: Generated script 'solr-instance'.", out)

        # No solrconfig.xml, schema.xml and stopwords.txt should be generated
        self.assertNotIn("solr-mc: Generated file 'solrconfig.xml'.", out)
        self.assertNotIn("solr-mc: Generated file 'schema.xml'.", out)
        self.assertNotIn("solr-mc: Generated file 'stopwords.txt'.", out)

        # ... and it's config files
        for core in ("core1", "core2"):
            aI("{0:s}: Generated file 'solrconfig.xml'.".format(core), out)
            aI("{0:s}: Generated file 'schema.xml'.".format(core), out)
            aI("{0:s}: Generated file 'stopwords.txt'.".format(core), out)

        # Jetty
        jetty_file = self.getfile("parts", "solr-mc", "etc", "jetty.xml")
        self.assertTrue(
            '<Set name="port"><SystemProperty name="jetty.port" default="1234" /></Set>'
            in jetty_file
        )  # noqa

        # Script
        solr_instance_script = self.getfile("bin", "solr-instance")
        chunk = "UPDATE_URL = r'http://127.0.0.1:1234/solr/update'"
        self.assertTrue(chunk in solr_instance_script)

        # Core 1
        with self.use_core("parts", "solr-mc", "solr", "core1") as c:

            aI('<field name="Foo" type="text" indexed="true"', c["schema"])
            aI('<field name="Bar" type="date" indexed="false"', c["schema"])
            aI('<field name="Foo bar" type="text" indexed="true"', c["schema"])
            aI('<field name="BlaWS" type="text_ws" indexed="true"', c["schema"])

            aI("<uniqueKey>uniqueID</uniqueKey>", c["schema"])
            self._test_field_types(c["schema"])

            aI('<int name="rows">55</int>', c["config"])
            aI(
                "<dataDir>{0:s}/var/solr/data/{1:s}</dataDir>".format(
                    self.globs["sample_buildout"], c["name"]
                ),
                c["config"],
            )

        with self.use_core("parts", "solr-mc", "solr", "core2") as c:

            aI('<field name="Foo" type="text" indexed="true"', c["schema"])
            aI('<field name="Bar" type="date" indexed="false"', c["schema"])
            aI('<field name="Foo bar" type="text" indexed="true"', c["schema"])
            self.assertNotIn(
                '<field name="BlaWS" type="text_ws" indexed="true"', c["schema"]
            )

            aI("<uniqueKey>uniqueID</uniqueKey>", c["schema"])
            self._test_field_types(c["schema"])

            aI('<int name="rows">99</int>', c["config"])
            aI(
                "<dataDir>{0:s}/var/solr/data/{1:s}</dataDir>".format(
                    self.globs["sample_buildout"], c["name"]
                ),
                c["config"],
            )

        with self.use_core("parts", "solr-mc", "solr", "core1") as c:
            self.assertIn(
                'class="${solr.directoryFactory:solr.' "StandardDirectoryFactory}",
                c["config"],
            )
        with self.use_core("parts", "solr-mc", "solr", "core2") as c:
            self.assertIn(
                'class="${solr.directoryFactory:solr.' "RAMDirectoryFactory}",
                c["config"],
            )

    def test_core_configuration_on_multicore_install(self):
        out = self._basic_multicore_install()

        # ... but solr.xml with core setup
        aI = self.assertIn
        aI("solr-mc: Generated file 'solr.xml'.", out)

        core_conf = self.getfile("parts", "solr-mc", "solr", "solr.xml")
        for core in ("core1", "core2"):
            aI('<core name="{0:s}" instanceDir="{0:s}" />'.format(core), core_conf)

    def test_install_is_not_called_on_update_if_instance_exists(self):
        # we test this on multicore setups, because they're setup are
        # equal among all supported solr versions.
        self._basic_multicore_install()
        conf = self.getpath(
            "parts", "solr-mc", "solr", "core1", "conf", "solrconfig.xml"
        )
        ctime = os.stat(conf).st_ctime
        time.sleep(1)
        self.globs["system"](self.globs["buildout"])
        self.assertEqual(os.stat(conf).st_ctime, ctime)

    def test_install_is_called_on_update_if_instance_not_exists(self):
        # we test this on multicore setups, because they're setup are
        # equal among all supported solr versions.
        self._basic_multicore_install()
        conf = self.getpath(
            "parts", "solr-mc", "solr", "core1", "conf", "solrconfig.xml"
        )
        ctime = os.stat(conf).st_ctime
        shutil.rmtree(self.getpath("parts", "solr-mc"))
        time.sleep(1)
        self.globs["system"](self.globs["buildout"])
        self.assertNotEqual(os.stat(conf).st_ctime, ctime)


class Solr40TestCase(Solr4xTestCase):
    """Test for Solr 4.0 - artifacts were prefixed with ``apache-``."""

    def create_sample_download_directories(self):
        super(Solr40TestCase, self).create_sample_download_directories()
        sample_buildout = self.globs["sample_buildout"]
        os.makedirs(os.path.join(sample_buildout, "dist", "apache-solr-4.0.war"))

    def test_artifact_prefix(self):
        self._basic_singlecore_install()

        # The `apache-` library prefix was removed in Solr 4.1.0,
        # see changelog here: http://bit.ly/1DVBqRC
        with self.use_core("parts", "solr", "solr", "collection1") as c:
            self.assertIn("apache-", c["config"])
