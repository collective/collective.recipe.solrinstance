# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os
import sys


version = "6.0.0b4.dev0"


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


requires = [
    "setuptools",
    "Genshi>=0.7.0",
    "hexagonit.recipe.download",
    "zc.buildout>=2.0.0a1",
    "zope.deprecation",
]

test_requires = requires + [
    "zope.exceptions",
    "zope.interface",
    "zope.testing",
]

if sys.version_info <= (2, 7):
    test_requires.append("unittest2")

long_description = "\n".join(
    [
        read("README.rst"),
        read("CHANGES.rst"),
        "Contributors",
        "************",
        read("CONTRIBUTORS.rst"),
        "Download",
        "********",
    ]
)


setup(
    name="collective.recipe.solrinstance",
    version=version,
    description="zc.buildout to configure a solr instance",
    long_description=long_description,
    classifiers=[
        "Framework :: Buildout",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="solr buildout recipe",
    author="Kai Lautaportti",
    author_email="kai.lautaportti@hexagonit.fi",
    url="http://pypi.python.org/pypi/collective.recipe.solrinstance",
    license="ZPL",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["collective", "collective.recipe"],
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require=dict(
        test=test_requires,
    ),
    test_suite="collective.recipe.solrinstance.tests.test_doctests.test_suite",
    # TODO: Remove the mc entry point in next major releases
    # since from collective.recip.solrinstance 6 it is identical to the default
    entry_points={
        "zc.buildout": [
            "default = collective.recipe.solrinstance:SolrRecipe",
            "mc = collective.recipe.solrinstance:MultiCoreSolrRecipe",
        ]
    },
)
