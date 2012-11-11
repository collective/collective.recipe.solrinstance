import unittest
import os
from textwrap import dedent
from os.path import join
from subprocess import check_output
from zc.buildout.testing import buildoutSetUp, buildoutTearDown
from zc.buildout.testing import install_develop


class TestSolr4(unittest.TestCase):
    globs = {}  # zc.buildout.testing needs this

    def setUp(self):
        buildoutSetUp(self)
        with open(join(self.globs['sample_buildout'], 'buildout.cfg'), 'w') as fh:
            fh.write(dedent("""
                [buildout]
                parts = solr

                [solr]
                recipe = collective.recipe.solrinstance
                host = 127.0.0.1
                port = 1234
                max-num-results = 99
                section-name = SOLR
                unique-key = uniqueID
                solr-version = 4
                index =
                    name:uniqueID type:string indexed:true stored:true required:true
                    name:Foo type:text
                    name:Bar type:date indexed:false stored:false required:true multivalued:true omitnorms:true
                    name:Foo bar type:text
                filter =
                    text solr.ISOLatin1AccentFilterFactory
                    text_ws Baz foo="bar" juca="bala"
            """))

        install_develop('zope.exceptions', self)
        install_develop('zope.interface', self)
        install_develop('zope.testing', self)
        install_develop('Cheetah', self)
        install_develop('Markdown', self)
        install_develop('iw.recipe.template', self)
        install_develop('collective.recipe.solrinstance', self)
        sample_buildout = self.globs['sample_buildout']
        os.makedirs(join(sample_buildout, 'example', 'etc'))
        os.makedirs(join(sample_buildout, 'example', 'solr', 'collection1', 'conf'))
        os.makedirs(join(sample_buildout, 'dist'))
        os.makedirs(join(sample_buildout, 'contrib'))

    def tearDown(self):
        buildoutTearDown(self)

    def test_basic_install(self):
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
        self.assertTrue(install_output in output)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSolr4))
    return suite
