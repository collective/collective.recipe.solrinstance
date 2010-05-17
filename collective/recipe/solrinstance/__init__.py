# -*- coding: utf-8 -*-
"""Recipe solrinstance"""

import zc.buildout
import iw.recipe.template
import shutil
import os

INDEX_TYPES = set(['text', 'text_ws', 'ignored', 'date', 'string',
                   'boolean', 'integer', 'long', 'float', 'double'])
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
                    'extras' : '',
                    'keepinzope' : 'true'}
DEFAULT_FILTERS = """
    text solr.StopFilterFactory ignoreCase="true" words="stopwords.txt"
    text solr.WordDelimiterFilterFactory generateWordParts="1" generateNumberParts="1" catenateWords="0" catenateNumbers="0" catenateAll="0"
    text solr.LowerCaseFilterFactory
    text solr.EnglishPorterFilterFactory protected="protwords.txt"
    text solr.RemoveDuplicatesTokenFilterFactory
"""
ZOPE_CONF = """
<product-config %(section-name)s>
    address %(host)s:%(port)s
    basepath %(basepath)s
</product-config>
"""
TRUE_VALUES = set(['yes', 'true', '1', 'on'])
TEMPLATE_DIR = os.path.dirname(__file__)

class Recipe(object):
    """This recipe is used by zc.buildout"""

    def __init__(self, buildout, name, options):
        self.name, self.options, self.buildout = name, options, buildout
        self.part_dir = os.path.join(buildout['buildout']['parts-directory'], name)

        options['host'] = options.get('host','localhost').strip()
        options['port'] = options.get('port', '8983').strip()
        options['basepath'] = options.get('basepath', '/solr').strip()
        options['section-name'] = options.get('section-name', 'solr').strip()
        options['solr-location'] = options.get('solr-location', '').strip()
        options['zope-conf'] = options.get('zope-conf', ZOPE_CONF % options).strip()

        options['jetty-destination'] = options.get(
            'jetty-destination',
            os.path.join(self.part_dir, 'etc'))

        options['config-destination'] = options.get(
            'config-destination',
            os.path.join(self.part_dir, 'solr', 'conf'))

        options['schema-destination'] = options.get(
            'schema-destination',
            os.path.join(self.part_dir, 'solr', 'conf'))

        options['vardir'] = options.get(
            'vardir',
            os.path.join(buildout['buildout']['directory'], 'var', 'solr'))

        options['logdir'] = options.get(
            'logdir',
            None)
        options['script'] = options.get('script', 'solr-instance').strip()

        try:
            num_results = int(options.get('max-num-results', '10').strip())
            if num_results < 1:
                raise ValueError
            options['max-num-results'] = str(num_results)
        except (ValueError, TypeError):
            raise zc.buildout.UserError(
                'Please use a positive integer for the number of default results')

        options['uniqueKey'] = options.get('unique-key', 'uid').strip()
        options['defaultSearchField'] = options.get('default-search-field', '').strip()
        options['defaultOperator'] = options.get('default-operator', 'OR').strip().upper()
        options['additional-solrconfig'] = options.get('additional-solrconfig', '').strip()
        options['requestParsers-multipartUploadLimitInKB'] = options.get('requestParsers-multipartUploadLimitInKB', '2048').strip()
        options['extraFieldTypes'] = options.get('extra-field-types', '')

        # Solr startup commands
        options['java_opts'] = options.get('java_opts', '')

    def parse_filter(self):
        """Parses the filter definitions from the options."""
        filters = {}
        for index in INDEX_TYPES:
            filters[index] = []
        for line in self.options.get('filter', DEFAULT_FILTERS).strip().splitlines():
            index, params = line.strip().split(' ', 1)
            parsed = params.strip().split(' ', 1)
            klass, extra = parsed[0], ''
            if len(parsed) > 1:
                extra = parsed[1]
            if index.lower() not in INDEX_TYPES:
                raise zc.buildout.UserError('Invalid index type: %s' % index)
            filters[index].append({'class': klass, 'extra': extra})
        return filters

    def _splitIndexLine(self, line):
        # Split an index line.
        # XXX should be implemented using re
        params = []
        for each in line.split():
            if each.find(':') == -1:
                # The former attr value contains a whitespace which is
                # allowed.
                if len(params) == 0:
                    raise zc.buildout.UserError(
                        'Invalid index definition: %s' % line)
                params[len(params)-1] += ' ' + each
            else:
                params.append(each)
        return params

    def parse_java_opts(self):
        """Parsed the java opts from `options`. """
        cmd_opts = []
        _start = ['java', '-jar']
        _jar = 'start.jar'
        _opts = []
        if not self.options['java_opts']:
            cmd_opts = _start
        else:
            _opts = self.options['java_opts'].strip().splitlines()
            cmd_opts = _start + _opts
        cmd_opts.append(_jar)
        return cmd_opts

    def parse_index(self):
        """Parses the index definitions from the options."""
        customTemplate = self.options.has_key('schema-template')
        indexAttrs = set(INDEX_ATTRIBUTES.keys())
        indeces = []
        names = []
        for line in self.options['index'].strip().splitlines():
            entry = {}
            for item in self._splitIndexLine(line):
                attr, value = item.split(':')[:2]
                if attr == 'copyfield':
                    entry.setdefault(attr, []).append(value)
                else:
                    entry[attr] = value

            keys = set(entry.keys())
            if not keys.issubset(indexAttrs):
                if customTemplate:
                    extras = []
                    for key in sorted(keys.difference(indexAttrs)):
                        extras.append('%s="%s"' % (key, entry[key]))
                    entry['extras'] = ' '.join(extras)
                else:
                    invalid = keys.difference(indexAttrs)
                    raise zc.buildout.UserError(
                        'Invalid index attribute(s): %s. '
                        'Allowed attributes are: %s.' %
                        (', '.join(invalid), ', '.join(indexAttrs)))

            if entry['name'] in names:
                raise zc.buildout.UserError(
                    'Duplicate name error: "%s" already defined.' % entry['name'])
            names.append(entry['name'])

            for key in INDEX_ATTRIBUTES:
                value = entry.get(key, INDEX_ATTRIBUTES[key])

                if key == 'copyfield':
                    entry[key] = [{'source':entry['name'], 'dest':val}
                                  for val in value]
                elif key in ('name', 'extras'):
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

        unique = self.options['uniqueKey']
        if unique and not unique in names:
            raise zc.buildout.UserError('Unique key without matching index: %s' % unique)
        if unique and not indeces[names.index(unique)].get('required', None) == 'true':
            raise zc.buildout.UserError('Unique key needs to be declared "required": %s' % unique)

        default = self.options['defaultSearchField']
        if default and not default in names:
            raise zc.buildout.UserError('Default search field without matching index: %s' % default)

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
        if self.options['script']:
            iw.recipe.template.Script(
                self.buildout,
                self.options['script'],
                kwargs).install()

    def install(self):
        """installer"""
        parts = [self.part_dir]

        if os.path.exists(self.part_dir):
            raise zc.buildout.UserError(
                'Target directory %s already exists. Please remove it.' % self.part_dir)

        # Copy the instance files
        shutil.copytree(os.path.join(self.options['solr-location'], 'example'), self.part_dir)

        solr_var = self.options['vardir']
        solr_data = os.path.join(solr_var, 'data')
        if options['logdir']:
            solr_log = self.options['logdir']
        else:
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
            source=self.options.get('config-template',
                '%s/templates/solrconfig.xml.tmpl' % TEMPLATE_DIR),
            datadir=solr_data,
            destination=self.options['config-destination'],
            rows=self.options['max-num-results'],
            additional_solrconfig=self.options['additional-solrconfig'],
            cacheSize=self.options.get('cacheSize'),
            useColdSearcher=self.options.get('useColdSearcher', 'false'),
            maxWarmingSearchers=self.options.get('maxWarmingSearchers', '4'),
            requestParsers_multipartUploadLimitInKB=self.options['requestParsers-multipartUploadLimitInKB'],
            )

        self.generate_solr_schema(
            source=self.options.get('schema-template',
                '%s/templates/schema.xml.tmpl' % TEMPLATE_DIR),
            destination=self.options['schema-destination'],
            filters=self.parse_filter(),
            indeces=self.parse_index(),
            options=self.options)

        self.create_bin_scripts(
            source='%s/templates/solr-instance.tmpl' % TEMPLATE_DIR,
            pidfile=os.path.join(solr_var, 'solr.pid'),
            logfile=os.path.join(solr_log, 'solr.log'),
            destination=self.buildout['buildout']['bin-directory'],
            solrdir=self.part_dir,
            startcmd=self.parse_java_opts())

        # returns installed files
        return parts

    def update(self):
        """updater"""
        pass
