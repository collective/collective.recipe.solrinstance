# -*- coding: utf-8 -*-
"""
Generic Test case for 'collective.recipe.solrinstance' doctest
"""
__docformat__ = 'restructuredtext'

import unittest
import doctest
import sys
import os

from zope.testing import doctest
import zc.buildout.testing

current_dir = os.path.dirname(__file__)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('collective.recipe.solrinstance', test)

def doc_suite(test_dir, setUp=None, tearDown=None, globs=None):
    """Returns a test suite, based on doctests found in /doctest."""
    suite = []
    if globs is None:
        globs = globals()

    globs['test_dir'] = current_dir

    flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE |
             doctest.REPORT_ONLY_FIRST_FAILURE)

    package_dir = os.path.split(test_dir)[0]
    if package_dir not in sys.path:
        sys.path.append(package_dir)

    suite.append(doctest.DocFileSuite('../README.txt', optionflags=flags,
                                  globs=globs, setUp=setUp,
                                  tearDown=tearDown,
                                  module_relative=True))

    return unittest.TestSuite(suite)

def test_suite():
    """returns the test suite"""
    return doc_suite(current_dir, setUp=setUp)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
