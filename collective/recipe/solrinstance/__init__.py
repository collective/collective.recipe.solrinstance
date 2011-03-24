# -*- coding: utf-8 -*-
"""Recipe solrinstance"""

import zc.buildout
import iw.recipe.template
import shutil
import os
import glob

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
                    'default' : '',
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
NOT_ALLOWED_ATTR = set(["index", "filter", "unique-key", "max-num-results", 
    "default-search-field", "default-operator", "additional-solrconfig", 
    "autoCommitMaxDocs", "autoCommitMaxTime" ,"requestParsers-multipartUploadLimitInKB",
    "cacheSize",
    ])

class SolrBase(object):
    """This class hold every base functions """

    def __init__(self, buildout, name, options_orig):
        self.name, self.options_orig, self.buildout = name, options_orig, buildout
        self.install_dir = os.path.join(buildout['buildout']['parts-directory'], name)
        self.instanceopts = self.initServerInstanceOpts(buildout, name, options_orig)

    def initServerInstanceOpts(self, buildout, name, options_orig):
        #server instance opts
        options = {}

        options['name'] = options_orig.get('name', name).strip()
        options['host'] = options_orig.get('host','localhost').strip()
        options['port'] = options_orig.get('port', '8983').strip()
        options['basepath'] = options_orig.get('basepath', '/solr').strip()
        options['solr-location'] = os.path.abspath(options_orig.get('solr-location', '').strip())
        options['jetty-template'] = options_orig.get("jetty-template", 
                '%s/templates/jetty.xml.tmpl' % TEMPLATE_DIR)

        options['jetty-destination'] = options_orig.get(
                'jetty-destination', os.path.join(self.install_dir, 'etc'))

        options['vardir'] = options_orig.get(
                'vardir',
                os.path.join(buildout['buildout']['directory'], 'var', 'solr'))

        options['logdir'] = options_orig.get(
                'logdir','')

        options['script'] = options_orig.get('script', 'solr-instance').strip()

        #XXX this is ugly and should be removed 
        options['section-name'] = options_orig.get('section-name', 'solr').strip()
        options_orig['zope-conf'] = options_orig.get('zope-conf', 
                ZOPE_CONF % options).strip()

        # Solr startup commands
        options['java_opts'] = options_orig.get('java_opts', '')
        return options

    def initSolrOpts(self, buildout, name, options_orig):
        #solr opts
        options = {}

        options['name'] = name
        options['index'] = options_orig.get('index')
        options['filter'] = options_orig.get('filter', DEFAULT_FILTERS).strip()
        options['config-template']=  options_orig.get('config-template',
                '%s/templates/solrconfig.xml.tmpl' % TEMPLATE_DIR)
        options["customTemplate"] = "schema-template" in options_orig
        options["schema-template"] = options_orig.get('schema-template',
                '%s/templates/schema.xml.tmpl' % TEMPLATE_DIR)
        options['config-destination'] = options_orig.get(
                'config-destination', 
                os.path.join(self.install_dir, 'solr', 'conf'))

        options['schema-destination'] = options_orig.get(
                'schema-destination', 
                os.path.join(self.install_dir, 'solr', 'conf'))

        try:
            num_results = int(options_orig.get('max-num-results', '10').strip())
            if num_results < 1:
                raise ValueError
            options['max-num-results'] = str(num_results)
        except (ValueError, TypeError):
            raise zc.buildout.UserError(
                'Please use a positive integer for the number of default results')

        options['uniqueKey'] = options_orig.get('unique-key', 'uid').strip()
        options['defaultSearchField'] = options_orig.get('default-search-field', '').strip()
        options['defaultOperator'] = options_orig.get('default-operator', 'OR').strip().upper()
        options['additional-solrconfig'] = options_orig.get('additional-solrconfig', '').strip()
        options['requestParsers-multipartUploadLimitInKB'] = options_orig.get('requestParsers-multipartUploadLimitInKB', '2048').strip()
        options['extraFieldTypes'] = options_orig.get('extra-field-types', '')

        options['autoCommitMaxDocs'] = options_orig.get('autoCommitMaxDocs', '')
        options['autoCommitMaxTime'] = options_orig.get('autoCommitMaxTime', '')
        return options

    def parse_filter(self, options):
        """Parses the filter definitions from the options."""
        filters = {}
        for index in INDEX_TYPES:
            filters[index] = []
        for line in options.get('filter').splitlines():
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

    def parse_java_opts(self, options):
        """Parsed the java opts from `options`. """
        cmd_opts = []
        _start = ['java', '-jar']
        _jar = 'start.jar'
        _opts = []
        if not options['java_opts']:
            cmd_opts = _start
        else:
            _opts = options['java_opts'].strip().splitlines()
            cmd_opts = _start + _opts
        cmd_opts.append(_jar)
        return cmd_opts

    def parse_index(self, options):
        """Parses the index definitions from the options."""
        indexAttrs = set(INDEX_ATTRIBUTES.keys())
        indeces = []
        names = []
        for line in options['index'].strip().splitlines():
            entry = {}
            for item in self._splitIndexLine(line):
                attr, value = item.split(':')[:2]
                if attr == 'copyfield':
                    entry.setdefault(attr, []).append(value)
                else:
                    entry[attr] = value

            keys = set(entry.keys())
            if not keys.issubset(indexAttrs):
                if options.get("customTemplate"):
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
                elif key in ('name', 'extras', 'default'):
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

        unique = options['uniqueKey']
        if unique and not unique in names:
            raise zc.buildout.UserError('Unique key without matching index: %s' % unique)
        if unique and not indeces[names.index(unique)].get('required', None) == 'true'\
                and indeces[names.index(unique)].get('default', "") == "":
            raise zc.buildout.UserError('Unique key needs to declared "required"=true or "default"=NEW: %s' % unique)

        default = options['defaultSearchField']
        if default and not default in names:
            raise zc.buildout.UserError('Default search field without matching index: %s' % default)

        return indeces

    def parseAutoCommit(self, options):
        mdocs = options['autoCommitMaxDocs']
        mtime = options['autoCommitMaxTime']
        if mdocs or mtime:
            result = ['<autoCommit>']
            if mdocs:
                result.append('<maxDocs>%s</maxDocs>' % str(mdocs))
            if mtime:
                result.append('<maxTime>%s</maxTime>' % str(mtime))
            result.append('</autoCommit>')
            return '\n'.join(result)
        return ''

    def generate_solr_mc(self, **kwargs):
        iw.recipe.template.Template(
            self.buildout,
            'solr.xml',
            kwargs).install()

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

    def create_bin_scripts(self, script, **kwargs):
        """ Create a runner for our solr instance """
        if script:
            iw.recipe.template.Script(
                self.buildout,
                script,
                kwargs).install()

    def copysolr(self, source, destination):
        # Copy the instance files
        shutil.copytree(source, destination)

    def copy_files(self, src_glob, dst_folder):
        for fname in glob.iglob(src_glob):
            try:
                shutil.copy(fname, dst_folder)
            except IOError,e:
                print e
    
    def create_mc_solr(self, path, cores, solr_var):
        """create a empty solr mc dir"""
        shutil.rmtree(os.path.join(path, 'solr'))
        os.makedirs(os.path.join(path, 'solr'))


class SolrSingleRecipe(SolrBase):
    """This recipe builds a single solr index"""

    def __init__(self, buildout, name, options_orig):
        super(SolrSingleRecipe, self).__init__(buildout, name, options_orig)
        self.solropts = self.initSolrOpts(buildout, name, options_orig)

    def install(self):
        """installer"""
        parts = [self.install_dir]

        if os.path.exists(self.install_dir):
            raise zc.buildout.UserError(
                'Target directory %s already exists. Please remove it.' % self.install_dir)

        # Copy the instance files
        self.copysolr(os.path.join(self.instanceopts['solr-location'], 'example'), self.install_dir)

        solr_var = self.instanceopts['vardir']
        solr_data = os.path.join(solr_var, 'data')
        if self.instanceopts['logdir']:
            solr_log = self.instanceopts['logdir']
        else:
            solr_log = os.path.join(solr_var, 'log')

        for path in solr_data, solr_log:
            if not os.path.exists(path):
                os.makedirs(path)

        self.generate_jetty(
            source=self.instanceopts.get('jetty-template'),
            logdir=solr_log,
            serverport=self.instanceopts['port'],
            destination=self.instanceopts['jetty-destination'])

        self.generate_solr_conf(
            source=self.solropts.get('config-template'),
            datadir=solr_data,
            destination=self.solropts['config-destination'],
            rows=self.solropts['max-num-results'],
            additional_solrconfig=self.solropts['additional-solrconfig'],
            cacheSize=self.solropts.get('cacheSize', '512'),
            useColdSearcher=self.solropts.get('useColdSearcher', 'false'),
            maxWarmingSearchers=self.solropts.get('maxWarmingSearchers', '4'),
            requestParsers_multipartUploadLimitInKB=self.solropts['requestParsers-multipartUploadLimitInKB'],
            autoCommit=self.parseAutoCommit(self.solropts),
            )

        self.generate_solr_schema(
            source=self.solropts.get('schema-template'),
            destination=self.solropts['schema-destination'],
            filters=self.parse_filter(self.solropts),
            indeces=self.parse_index(self.solropts),
            options=self.solropts)

        self.create_bin_scripts(
            self.instanceopts.get('script'),
            source='%s/templates/solr-instance.tmpl' % TEMPLATE_DIR,
            pidfile=os.path.join(solr_var, 'solr.pid'),
            logfile=os.path.join(solr_log, 'solr.log'),
            destination=self.buildout['buildout']['bin-directory'],
            solrdir=self.install_dir,
            startcmd=self.parse_java_opts(self.instanceopts))

        # returns installed files
        return parts

    def update(self):
        """updater"""

        if os.path.exists(self.install_dir):
            shutil.rmtree(self.install_dir)

        return self.install()


class MultiCoreRecipe(SolrBase):
    """Builds a multicore solr without any instances"""

    def __init__(self, buildout, name, options):
        super(MultiCoreRecipe, self).__init__(buildout, name, options)
        if "cores" not in options:
            raise zc.buildout.UserError('Attribute `cores` not defined.')
        try:
            self.cores = [x for x in options["cores"].split(" ") if len(x) > 0]
        except:
            raise zc.buildout.UserError(
                    'Attribute `cores` not correct defined. Define as withespace seperated list `cores = X1 X2 X3`')
        if not self.cores:
            raise zc.buildout.UserError(
                    'Attribute `cores` not correct defined. Define as withespace seperated list `cores = X1 X2 X3`')
        not_allowed_attr = set(self.options_orig.keys()) & NOT_ALLOWED_ATTR

        if len(not_allowed_attr) != 0:
            raise zc.buildout.UserError(
                    'Core attributes are not allowed in multicore recipe')

    def install(self):
        """installer"""
        parts = [self.install_dir]

        if os.path.exists(self.install_dir):
            raise zc.buildout.UserError(
                'Target directory %s already exists. Please remove it.' % self.install_dir)

        # Copy the instance files
        self.copysolr(os.path.join(self.instanceopts['solr-location'], 'example'), self.install_dir)
        
        solr_var = self.instanceopts['vardir']
        if self.instanceopts['logdir']:
            solr_log = self.instanceopts['logdir']
        else:
            solr_log = os.path.join(solr_var, 'log')

        if not os.path.exists(solr_log):
            os.makedirs(solr_log)

        # rm solr example and create a empty one
        self.create_mc_solr(self.install_dir, self.cores, solr_var)

        solr_dir = os.path.join(self.install_dir, 'solr')
        self.generate_solr_mc(
            source='%s/templates/solr.xml.tmpl' % TEMPLATE_DIR,
            cores=self.cores,
            destination=solr_dir)

        #generate defined cores
        for core in self.cores:
            options_core = self.buildout[core]
            options_core = self.initSolrOpts(self.buildout, core, self.buildout[core])
            conf_dir = os.path.join(solr_dir, core, "conf")

            if not os.path.exists(conf_dir):
                os.makedirs(conf_dir)

            self.copy_files(os.path.join(
                self.instanceopts['solr-location'], 'example', 'solr', 'conf', '*.txt'), 
                conf_dir)

            solr_data = os.path.join(solr_var, 'data', core)
            if not os.path.exists(solr_data):
                os.makedirs(solr_data)

            self.generate_solr_conf(
                source=options_core.get('config-template',
                    '%s/templates/solrconfig.xml.tmpl' % TEMPLATE_DIR),
                datadir=solr_data,
                destination=conf_dir,
                rows=options_core['max-num-results'],
                additional_solrconfig=options_core['additional-solrconfig'],
                cacheSize=options_core.get('cacheSize', '512'),
                useColdSearcher=options_core.get('useColdSearcher', 'false'),
                maxWarmingSearchers=options_core.get('maxWarmingSearchers', '4'),
                requestParsers_multipartUploadLimitInKB=options_core['requestParsers-multipartUploadLimitInKB'],
                autoCommit=self.parseAutoCommit(options_core),
                )

            self.generate_solr_schema(
                source=options_core.get('schema-template',
                    '%s/templates/schema.xml.tmpl' % TEMPLATE_DIR),
                destination=conf_dir,
                filters=self.parse_filter(options_core),
                indeces=self.parse_index(options_core),
                options=options_core)

        self.generate_jetty(
            source=self.instanceopts.get('jetty-template',
                     '%s/templates/jetty.xml.tmpl' % TEMPLATE_DIR),
            logdir=solr_log,
            serverport=self.instanceopts['port'],
            destination=self.instanceopts['jetty-destination'])

        self.create_bin_scripts(
            self.instanceopts.get('script'),
            source='%s/templates/solr-instance.tmpl' % TEMPLATE_DIR,
            pidfile=os.path.join(solr_var, 'solr.pid'),
            logfile=os.path.join(solr_log, 'solr.log'),
            destination=self.buildout['buildout']['bin-directory'],
            solrdir=self.install_dir,
            startcmd=self.parse_java_opts(self.instanceopts))

        # returns installed files
        return parts

    def update(self):
        """updater"""

        if os.path.exists(self.install_dir):
            shutil.rmtree(self.install_dir)

        return self.install()

