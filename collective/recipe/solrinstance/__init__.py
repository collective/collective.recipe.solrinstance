# -*- coding: utf-8 -*-
"""Recipe solrinstance"""

import logging
import zc.buildout
import iw.recipe.template
import shutil
import os
import sys

INDEX_TYPES = set(['text', 'text_ws', 'keyword', 'date', 'string'])
INDEX_ATTRIBUTES = {'name' : '',
                    'type' : '',
                    'copyfield' : [],
                    'sortable' : 'false',
                    'auto' : 'false',
                    'omitnorms' : 'false',
                    'multivalued' : 'false',
                    'required' : 'false',
                    'indexed' : 'true',
                    'stored' : 'true',
                    'keepinzope' : 'true'}
TRUE_VALUES = set(['yes', 'true', '1', 'on'])
TEMPLATE_DIR = os.path.dirname(__file__)

class Recipe(object):
    """This recipe is used by zc.buildout"""

    def __init__(self, buildout, name, options):
        self.name, self.options, self.buildout = name, options, buildout
        self.part_dir = os.path.join(buildout['buildout']['parts-directory'], name)

        options['address'] = options.get('address','').strip()
        options['port'] = options.get('port', '').strip()
        options['basepath'] = options.get('basepath', '/').strip()
        options['solr-location'] = options.get('solr-location', '').strip()

        options['jetty-destination'] = options.get(
            'jetty-destination',
            os.path.join(self.part_dir, 'etc'))

        options['config-destination'] = options.get(
            'config-destination',
            os.path.join(self.part_dir, 'solr', 'conf'))

        options['schema-destination'] = options.get(
            'schema-destination',
            os.path.join(self.part_dir, 'solr', 'conf'))

        try:
            num_results = int(options.get('max-num-results').strip(), 10)
            if num_results < 1:
                raise ValueError
            options['max-num-results'] = str(num_results)
        except (ValueError, TypeError):
            raise zc.buildout.UserError(
                'Please use a positive integer for the number of default results')

    def parse_index(self):
        """Parses the index definitions from the options."""
        indeces = []
        names = []

        for line in self.options['index'].strip().splitlines():
            entry = {}
            for item in line.split():
                attr, value = item.split(':')[:2]
                if attr == 'copyfield':
                    entry.setdefault(attr, []).append(value)
                else:
                    entry[attr] = value

            if not set(entry.keys()).issubset(set(INDEX_ATTRIBUTES.keys())):
                raise zc.buildout.UserError(
                    'Invalid index attribute(s). Allowed attributes are %s' % (', '.join(INDEX_ATTRIBUTES.keys()))) 

            if entry['type'].lower() not in INDEX_TYPES:
                raise zc.buildout.UserError('Invalid index type: %s' % entry['type'])

            if entry['name'] in names:
                raise zc.buildout.UserError(
                    'Duplicate name error: "%s" already defined.' % entry['name'])
            names.append(entry['name'])

            for key in INDEX_ATTRIBUTES:
                value = entry.get(key, INDEX_ATTRIBUTES[key])

                if key == 'copyfield':
                    entry[key] = [{'source':entry['name'], 'dest':val}
                                  for val in value]
                elif key == 'name':
                    entry[key] = value
                elif key == 'type':
                    entry[key] = value.lower()
                else:
                    if value.strip() in TRUE_VALUES:
                        value = 'true'
                    else:
                        value = 'false' 
                    entry[key] = value

            indeces.append(entry)

        return indeces

    def generate_jetty(self, **kwargs):
        iw.recipe.template.Template(
            self.buildout,
            'jetty.xml',
            kwargs).install()

    def generate_solr_conf(self, **kwargs):
        iw.recipe.template.Template(
            self.buildout,
            'solrconfig.xml',
            kwargs).install()

    def generate_solr_schema(self, **kwargs):
        iw.recipe.template.Template(
            self.buildout,
            'schema.xml',
            kwargs).install()

    def create_bin_scripts(self, **kwargs):
        """ Create a runner for our solr instance """
        iw.recipe.template.Script(
                self.buildout,
                'solr-instance',
                kwargs
                ).install()


    def install(self):
        """installer"""
        parts = [self.part_dir]

        if os.path.exists(self.part_dir):
            raise zc.buildout.UserError(
                'Target directory %s already exists. Please remove it.' % self.part_dir)

        # Copy the instance files
        shutil.copytree(os.path.join(self.options['solr-location'], 'example'), self.part_dir)

        solr_var = os.path.join(
                self.buildout['buildout']['directory'], 'var', 'solr')

        solr_data = os.path.join(solr_var, 'data')
        solr_log = os.path.join(solr_var, 'log')

        for path in solr_data, solr_log:
            if not os.path.exists(path):
                os.makedirs(path)

        self.generate_jetty(
            source='%s/templates/jetty.xml.tmpl' % TEMPLATE_DIR,
            logdir=solr_log,
            serverport=self.options['port'],
            destination=self.options['jetty-destination'])

        self.generate_solr_conf(
            source='%s/templates/solrconfig.xml.tmpl' % TEMPLATE_DIR,
            datadir=solr_data,
            destination=self.options['config-destination'],
            rows=self.options['max-num-results'])

        self.generate_solr_schema(
            source='%s/templates/schema.xml.tmpl' % TEMPLATE_DIR,
            destination=self.options['schema-destination'],
            indeces=self.parse_index())

        self.create_bin_scripts(
            source='%s/templates/solr-instance.tmpl' % TEMPLATE_DIR,
            pidfile=os.path.join(solr_var, 'solr.pid'),
            # work around a bug in iw.recipe.template
            destination=self.buildout['buildout']['bin-directory'],
            solrdir=os.path.join(self.options['solr-location'], 'example')
            )

        # returns installed files
        return parts

    def update(self):
        """updater"""
        pass
