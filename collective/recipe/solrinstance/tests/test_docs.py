"""
Generic Test case for 'collective.recipe.solrinstance' doctest
"""

import unittest
import doctest
import sys
import os

from zope.testing import doctestunit
import zc.buildout.testing

flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE |
         doctest.REPORT_ONLY_FIRST_FAILURE)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('collective.recipe.solrinstance', test)

def test_suite():
    """ returns the test suite """
    return unittest.TestSuite([
        doctestunit.DocFileSuite(
           'README.txt', package='collective.recipe.solrinstance',
           optionflags=flags, setUp=setUp)
    ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

