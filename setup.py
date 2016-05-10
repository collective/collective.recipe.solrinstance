# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages

version = '5.3.3'


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


requires = ['setuptools']
if sys.version_info >= (3,):
    requires += [
        'Genshi>=0.7.0',
        'zc.buildout>=2.0.0a1',
        ]
else:
    requires += [
        'Genshi',
        'zc.buildout',
        ]
test_requires = requires + [
    'zope.exceptions',
    'zope.interface',
    'zope.testing',
]


setup(
    name='collective.recipe.solrinstance',
    version=version,
    description="zc.buildout to configure a solr instance",
    long_description=(
        read('README.rst')
        + '\n' +
        read('CHANGES.rst')
        + '\n' +
        'Contributors\n'
        '***********************\n'
        + '\n' +
        read('CONTRIBUTORS.rst')
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
    package_data={
        'collective.recipe.solrinstance': ['templates/*', 'templates4/*'],
    },
    zip_safe=False,
    install_requires=requires,
    setup_requires=[
        'setuptools',
        'setuptools-git',
    ],
    tests_require=test_requires,
    extras_require=dict(
        test=test_requires,
    ),
    test_suite='collective.recipe.solrinstance.tests.test_doctests.test_suite',
    entry_points={
        "zc.buildout": [
            "default = collective.recipe.solrinstance:SolrSingleRecipe",
            "mc = collective.recipe.solrinstance:MultiCoreRecipe",
        ]
    },
)
