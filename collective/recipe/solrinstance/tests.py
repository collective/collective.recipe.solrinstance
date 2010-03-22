"""
Generic Test case for 'collective.recipe.solrinstance' doctest
"""

from unittest import TestSuite
from doctest import COMPARISON_FLAGS, NORMALIZE_WHITESPACE
from zope.testing import doctestunit
from zc.buildout.testing import buildoutSetUp, install_develop


def setUp(test):
    buildoutSetUp(test)
    install_develop('zope.exceptions', test)
    install_develop('zope.interface', test)
    install_develop('zope.testing', test)
    install_develop('Cheetah', test)
    install_develop('Markdown', test)
    install_develop('iw.recipe.template', test)
    install_develop('collective.recipe.solrinstance', test)

def test_suite():
    """ returns the test suite """
    return TestSuite([
        doctestunit.DocFileSuite(
           'README.txt', package='collective.recipe.solrinstance',
           optionflags=COMPARISON_FLAGS | NORMALIZE_WHITESPACE, setUp=setUp)
    ])
