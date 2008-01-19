# -*- coding: utf-8 -*-
"""Recipe solrinstance"""

import logging
import zc.buildout
import iw.recipe.template
import os

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

        options['address'] = options.get('address','').strip()
        options['port'] = options.get('port', '').strip()
        options['basepath'] = options.get('basepath', '/').strip()
        options['solr-location'] = options.get('solr-location', '').strip()

        options['jetty-destination'] = options.get(
            'jetty-destination',
            os.path.join(options['solr-location'], 'example', 'etc'))

        options['config-destination'] = options.get(
            'config-destination',
            os.path.join(options['solr-location'], 'example', 'solr', 'conf'))

        options['schema-destination'] = options.get(
            'schema-destination',
            os.path.join(options['solr-location'], 'example', 'solr', 'conf'))

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

    def create_bin_scripts(self):
        """ Create a runner for our solr instance """
        bintarget = self.buildout['buildout']['bin-directory']
        target = os.path.join(bintarget, self.name)

        python = self.buildout['buildout']['python']
        executable = self.buildout[python]['executable']

        f = open(target, 'wt')
        print >> f, "#!%s\n" % executable
        print >> f, "import os"
        print >> f, "os.chdir('%s')" % os.path.join(
                self.buildout['buildout']['directory'],
                self.options['solr-location'], 'example')
        print >> f, "os.system('java -jar start.jar')"
        os.chmod(target, 0755)
        self.options.created(target)

    def install(self):
        """installer"""

        solr_data = os.path.join(
                self.buildout['buildout']['directory'], 'var', 'solr', 'data')
        solr_log = os.path.join(
                self.buildout['buildout']['directory'], 'var', 'solr', 'log')

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
            destination=self.options['config-destination'])

        self.generate_solr_schema(
            source='%s/templates/schema.xml.tmpl' % TEMPLATE_DIR,
            destination=self.options['schema-destination'],
            indeces=self.parse_index())

        self.create_bin_scripts()

        # returns installed files
        return tuple()

    def update(self):
        """updater"""
        pass