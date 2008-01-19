# -*- coding: utf-8 -*-
"""
This module contains the tool of collective.recipe.solrinstance
"""
import os
from setuptools import setup, find_packages

version = '0.1'

README = os.path.join(os.path.dirname(__file__),
                      'collective',
                      'recipe',
                      'solrinstance', 'docs', 'README.txt')

long_description = open(README).read() + '\n\n'

entry_point = 'collective.recipe.solrinstance:Recipe'

entry_points = {"zc.buildout": ["default = %s" % entry_point]}

setup(name='collective.recipe.solrinstance',
      version=version,
      description="zc.buildout to configure a solr instance",
      long_description=long_description,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Kai Lautaportti',
      author_email='kai.lautaportti@hexagonit.fi',
      url='',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'iw.recipe.template',
                        'zc.buildout'
                        # -*- Extra requirements: -*-
                        ],
      tests_require=['zope.testing'],
      entry_points=entry_points,
      )
