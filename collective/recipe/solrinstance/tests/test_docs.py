"""
Generic Test case for 'collective.recipe.solrinstance' doctest
"""

from unittest import TestSuite, main
from doctest import COMPARISON_FLAGS
from zope.testing import doctestunit
from zc.buildout.testing import buildoutSetUp, install_develop

def setUp(test):
    buildoutSetUp(test)
    install_develop('zope.testing', test)
    install_develop('iw.recipe.template', test)
    install_develop('collective.recipe.solrinstance', test)

def test_suite():
    """ returns the test suite """
    return TestSuite([
        doctestunit.DocFileSuite(
           'README.txt', package='collective.recipe.solrinstance',
           optionflags=COMPARISON_FLAGS, setUp=setUp)
    ])

if __name__ == '__main__':
    main(defaultTest='test_suite')

