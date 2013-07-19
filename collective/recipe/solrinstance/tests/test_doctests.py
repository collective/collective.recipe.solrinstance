import os
from doctest import ELLIPSIS, NORMALIZE_WHITESPACE, REPORT_UDIFF
from doctest import DocFileSuite

from zc.buildout.testing import buildoutSetUp, buildoutTearDown
from zc.buildout.testing import install_develop


def setUp(test):
    buildoutSetUp(test)
    #Work around "Not Found" messages on Buildout 2
    del os.environ['buildout-testing-index-url']
    test.globs['buildout'] += ' -No'

    install_develop('zope.exceptions', test)
    install_develop('zope.interface', test)
    install_develop('zope.testing', test)
    install_develop('genshi', test)
    install_develop('collective.recipe.solrinstance', test)


def test_suite():
    return DocFileSuite(
           '../README.txt',
           setUp=setUp, tearDown=buildoutTearDown,
           optionflags=ELLIPSIS | NORMALIZE_WHITESPACE | REPORT_UDIFF)
