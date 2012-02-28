# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

version = '3.7.1'

def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


setup(name='collective.recipe.solrinstance',
      version=version,
      description="zc.buildout to configure a solr instance",
      long_description= (
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Contributors\n'
        '***********************\n'
        + '\n' +
        read('CONTRIBUTORS.txt')
        + '\n' +
        'Download\n'
        '***********************\n'),
      classifiers=[
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Topic :: Software Development :: Build Tools',
        ],
      keywords='',
      author='Kai Lautaportti',
      author_email='kai.lautaportti@hexagonit.fi',
      url='http://pypi.python.org/pypi/collective.recipe.solrinstance',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'iw.recipe.template',
        'zc.buildout'],
      tests_require=[
        'zope.exceptions',
        'zope.interface',
        'zope.testing'],
      test_suite = 'collective.recipe.solrinstance.tests.test_suite',
      entry_points = {
        "zc.buildout": ["default = collective.recipe.solrinstance:SolrSingleRecipe",
                        "mc = collective.recipe.solrinstance:MultiCoreRecipe",
                        ]
        },
      )
