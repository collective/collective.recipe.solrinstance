# -*- coding: utf-8 -*-

import glob
import logging
import os
import shutil
import sys

from genshi.template import Context, NewTextTemplate
from genshi.template.base import TemplateSyntaxError
from genshi.template.eval import UndefinedError
import pkg_resources
import zc.buildout


INDEX_TYPES = set(['text', 'text_ws', 'ignored', 'date', 'string',
                   'boolean', 'integer', 'long', 'float', 'double'])

INDEX_ATTRIBUTES = {'name': '',
                    'type': '',
                    'copyfield': [],
                    'sortable': 'false',
                    'auto': 'false',
                    'omitnorms': '',
                    'multivalued': 'false',
                    'required': 'false',
                    'indexed': 'true',
                    'stored': 'true',
                    'termVectors': 'false',
                    'termPositions': 'false',
                    'termOffsets': 'false',
                    'extras': '',
                    'default': '',
                    'keepinzope': 'true',
                    'storeOffsetsWithPositions': ''}

DEFAULT_FILTERS = """
    text solr.ICUFoldingFilterFactory
    text solr.WordDelimiterFilterFactory splitOnCaseChange="0" splitOnNumerics="0" stemEnglishPossessive="0" preserveOriginal="1"
    text solr.TrimFilterFactory
    text solr.StopFilterFactory ignoreCase="true" words="stopwords.txt"
"""
DEFAULT_CHAR_FILTERS = """
"""
DEFAULT_TOKENIZER = """
    text solr.ICUTokenizerFactory
    text_ws solr.WhitespaceTokenizerFactory
"""

#: Processors that allow just one entry per field type
UNIQUE_PROCESSORS = ('tokenizer',)

ZOPE_CONF = """
<product-config %(section-name)s>
    address %(host)s:%(port)s
    basepath %(basepath)s
</product-config>
"""

TRUE_VALUES = set(['yes', 'true', '1', 'on'])
TEMPLATE_DIR = os.path.dirname(__file__)
NOT_ALLOWED_ATTR = set(["index", "filter", "unique-key", "max-num-results",
                        "default-search-field", "default-operator",
                        "additional-solrconfig",
                        "additional-solrconfig-query",
                        "autoCommitMaxDocs", "autoCommitMaxTime", "updateLog",
                        "requestParsers-multipartUploadLimitInKB",
                        "requestParsers-enableRemoteStreaming"])


class SolrBase(object):
    """This class hold every base functions """

    def __init__(self, buildout, name, options_orig):
        self.generated = []
        self.name = name
        self.options_orig = options_orig
        self.solr_location = os.path.abspath(
            options_orig.get('solr-location', '').strip())
        self.buildout = buildout
        self.install_dir = os.path.join(
            buildout['buildout']['parts-directory'], name)
        self.instanceopts = self.initServerInstanceOpts(buildout, name,
                                                        options_orig)

        # let other recipies reference the destination path
        options_orig['location'] = self.install_dir
        self.logger = logging.getLogger(self.name)

    def initServerInstanceOpts(self, buildout, name, options_orig):
        #server instance opts
        options = {}

        options['name'] = options_orig.get('name', name).strip()
        options['host'] = options_orig.get('host', 'localhost').strip()
        options['port'] = options_orig.get('port', '8983').strip()
        options['basepath'] = options_orig.get('basepath', '/solr').strip()
        options['solr-location'] = os.path.abspath(
            options_orig.get('solr-location', '').strip())
        options['jetty-template'] = options_orig.get("jetty-template")
        options['log4j-template'] = options_orig.get("log4j-template")
        options['logging-template'] = options_orig.get("logging-template")

        options['jetty-destination'] = options_orig.get('jetty-destination')

        options['vardir'] = options_orig.get(
                'vardir',
                os.path.join(buildout['buildout']['directory'], 'var', 'solr'))

        options['logdir'] = options_orig.get('logdir', '')

        options['script'] = options_orig.get('script', 'solr-instance').strip()

        options['pidpath'] = options_orig.get('pidpath', '')

        #XXX this is ugly and should be removed
        options['section-name'] = options_orig.get('section-name',
                                                   'solr').strip()
        options_orig['zope-conf'] = options_orig.get('zope-conf',
                ZOPE_CONF % options).strip()

        # Solr startup commands
        options['java_opts'] = options_orig.get('java_opts', '')
        return options

    def get_artifact_prefix(self):
        test_artifacts = os.path.join(self.solr_location, 'dist', 'apache-*')
        if not self.is_solr_4() or glob.glob(test_artifacts):
            return 'apache-'
        return ''

    def is_solr_4(self):
        sol4_dir = os.path.join('example', 'solr', 'collection1')
        return os.path.isdir(os.path.join(self.solr_location, sol4_dir))

    @property
    def tpldir(self):
        value = os.path.join(TEMPLATE_DIR, 'templates')
        if self.is_solr_4():
            value += '4'
        return value

    def initSolrOpts(self, buildout, name, options_orig):
        #solr opts
        options = {'analyzers': {},
                   'artifact_prefix': self.get_artifact_prefix()}

        options['name'] = name
        options['index'] = options_orig.get('index')

        filter = options_orig.get('filter', DEFAULT_FILTERS).strip()
        char_filter = options_orig.get('char-filter',
                                       DEFAULT_CHAR_FILTERS).strip()
        options['extra_conf_files'] = options_orig.get(
            'extra-conf-files', "").strip().splitlines()
        tokenizer = options_orig.get('tokenizer', DEFAULT_TOKENIZER).strip()
        for analyzer_type in ('query', 'index'):
            options['analyzers'][analyzer_type] = {'filter': filter,
                                                   'char_filter': char_filter,
                                                   'tokenizer': tokenizer}
            for proc in ('filter', 'char-filter', 'tokenizer'):
                #Options are stored like 'filter-query' and 'filter-index'
                processor = '{0}-{1}'.format(proc, analyzer_type)
                proc_store = proc.replace('-', '_')
                options['analyzers'][analyzer_type][proc_store] += \
                        ('\n    ' + options_orig.get(processor, '').strip())

        options['config-template'] = options_orig.get('config-template')
        options["customTemplate"] = "schema-template" in options_orig
        options["schema-template"] = options_orig.get('schema-template', '')
        options['stopwords-template'] = options_orig.get('stopwords-template', '')
        options['config-destination'] = options_orig.get('config-destination')
        options['schema-destination'] = options_orig.get('schema-destination')

        try:
            num_results = int(options_orig.get('max-num-results',
                                               '500').strip())
            if num_results < 1:
                raise ValueError
            options['max-num-results'] = str(num_results)
        except (ValueError, TypeError):
            raise zc.buildout.UserError('Please use a positive integer '
                                        'for the number of default results')

        options['uniqueKey'] = options_orig.get('unique-key', 'uid').strip()
        options['defaultSearchField'] = options_orig.get(
            'default-search-field', '').strip()
        options['defaultOperator'] = options_orig.get(
            'default-operator', 'OR').strip().upper()
        options['additional-solrconfig'] = options_orig.get(
            'additional-solrconfig', '').strip()
        options['additional-solrconfig-query'] = options_orig.get(
            'additional-solrconfig-query', '').strip()
        options['additionalSchemaConfig'] = options_orig.get(
            'additional-schema-config', '').strip()
        options['requestParsers-multipartUploadLimitInKB'] = options_orig.get(
            'requestParsers-multipartUploadLimitInKB', '102400').strip()
        options['requestParsers-enableRemoteStreaming'] = options_orig.get(
            'requestParsers-enableRemoteStreaming', 'false'
        )
        options['extraFieldTypes'] = options_orig.get('extra-field-types', '')

        options['mergeFactor'] = options_orig.get('mergeFactor', '10')
        options['ramBufferSizeMB'] = options_orig.get('ramBufferSizeMB', '16')
        options['unlockOnStartup'] = options_orig.get('unlockOnStartup',
                                                      'true')
        options['spellcheckField'] = options_orig.get('spellcheckField',
                                                      'default')
        options['autoCommitMaxDocs'] = options_orig.get('autoCommitMaxDocs',
                                                        '')
        options['autoCommitMaxTime'] = options_orig.get('autoCommitMaxTime',
                                                        '')
        options['updateLog'] = options_orig.get(
            'updateLog', 'false').strip().lower() in TRUE_VALUES

        options['filterCacheSize'] = options_orig.get('filterCacheSize',
                                                      '16384')
        options['filterCacheInitialSize'] = options_orig.get(
            'filterCacheInitialSize', '4096')
        options['filterCacheAutowarmCount'] = options_orig.get(
            'filterCacheAutowarmCount', '4096')
        options['queryResultCacheSize'] = options_orig.get(
            'queryResultCacheSize', '128')
        options['queryResultCacheInitialSize'] = options_orig.get(
            'queryResultCacheInitialSize', '64')
        options['queryResultCacheAutowarmCount'] = options_orig.get(
            'queryResultCacheAutowarmCount', '32')
        options['documentCacheSize'] = options_orig.get(
            'documentCacheSize', '512')
        options['documentCacheInitialSize'] = options_orig.get(
            'documentCacheInitialSize', '512')
        options['documentCacheAutowarmCount'] = options_orig.get(
            'documentCacheAutowarmCount', '0')
        options['directoryFactory'] = options_orig.get(
            'directoryFactory', 'solr.NRTCachingDirectoryFactory')
        options['additionalFieldConfig'] = options_orig.get(
            'additionalFieldConfig', '')

        options['extralibs'] = []
        extralibs = options_orig.get('extralibs', '').strip()
        for lib in extralibs.splitlines():
            if ':' in lib:
                path, regex = lib.split(':', 1)
            else:
                path = lib
                regex = ".*\.jar"
            if path.strip():
                options['extralibs'].append({'path': path, 'regex': regex})
        options['abortOnConfigurationError'] = \
            options_orig.get('abortOnConfigurationError', 'false')

        return options

    def parse_processor(self, filter_option, unique=False):
        """Parses the processor (char filter, filter, tokenizer) definitions.

        String-based options are parsed to obtain class and option definitions
        for field types. If the `unique` option is enabled, only the last
        option is stored."""
        filters = {}
        for index in INDEX_TYPES:
            filters[index] = []
        for line in filter_option.splitlines():
            line_stripped = line.strip()
            if line_stripped:
                index, params = line_stripped.split(' ', 1)
                parsed = params.strip().split(' ', 1)
                klass, extra = parsed[0], ''
                if len(parsed) > 1:
                    extra = parsed[1]
                if index.lower() not in INDEX_TYPES:
                    raise zc.buildout.UserError('Invalid index type: %s' % index)

                filter = {'class': klass, 'extra': extra}
                if unique:
                    filters[index] = [filter]
                else:
                    filters[index].append(filter)
        return filters

    def parse_analyzer(self, options):
        """Parse all analyzers and their configuration from the options."""
        analyzers = {}
        for analyzer_type in options['analyzers']:
            analyzers[analyzer_type] = {}
            analyzer_options = options['analyzers'][analyzer_type]
            for processor in analyzer_options:
                unique = processor in UNIQUE_PROCESSORS
                analyzers[analyzer_type][processor] = \
                        self.parse_processor(analyzer_options[processor],
                                             unique=unique)
        return analyzers

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
                params[len(params) - 1] += ' ' + each
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
            if line.strip().startswith('#'):
                continue  # Allow comments
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
                    'Duplicate name error: "%s" already defined.' %
                    entry['name'])
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
                elif key in ('omitnorms',
                             'storeOffsetsWithPositions') and not value:
                    # don't override omitNorms default value
                    entry[key] = value
                else:
                    if value.strip() in TRUE_VALUES:
                        value = 'true'
                    else:
                        value = 'false'
                    entry[key] = value

            indeces.append(entry)

        unique = options['uniqueKey']
        if unique and not unique in names:
            raise zc.buildout.UserError('Unique key without matching '
                                        'index: %s' % unique)
        if (unique and not
            indeces[names.index(unique)].get('required', None) == 'true' and
            indeces[names.index(unique)].get('default', "") == ""):
            raise zc.buildout.UserError('Unique key needs to declared '
                                        '"required"=true or "default"=NEW: '
                                        '%s' % unique)

        default = options['defaultSearchField']
        if default and not default in names:
            raise zc.buildout.UserError('Default search field without '
                                        'matching index: %s' % default)

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

    def _generate_from_template(self, executable=False, **kwargs):
        destination = kwargs['destination']
        source = kwargs['source']
        name = kwargs['name']
        output_file = os.path.join(destination, name)
        with open(source, 'r') as template:
            template = NewTextTemplate(template)

        context = Context(name=name, buildout=self.buildout, options=kwargs)
        try:
            output = template.generate(context).render()
        except (TemplateSyntaxError, UndefinedError) as e:
            raise zc.buildout.UserError("Error in template %s:\n%s" %
                                        (name, e.msg))

        if executable:
            output = '#!%s\n%s' % (sys.executable, output)

        if executable and sys.platform == 'win32':
            exe = output_file + '.exe'
            open(exe, 'wb').write(
                pkg_resources.resource_string('setuptools', 'cli.exe')
            )
            self.generated.append(exe)
            output_file = output_file + '-script.py'

        with open(output_file, 'wb') as outfile:
            outfile.write(output.encode('utf8'))

        if executable:
            self.logger.info("Generated script %r.", name)
            try:
                os.chmod(output_file, 493)  # 0755 / 0o755
            except (AttributeError, os.error):
                pass
        else:
            self.logger.info("Generated file %r.", name)

        self.generated.append(output_file)

    def generate_solr_mc(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='solr.xml', **kwargs)

    def generate_jetty(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='jetty.xml', **kwargs)

    def generate_log4j(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='log4j.properties', **kwargs)

    def generate_logging(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='logging.properties', **kwargs)

    def generate_solr_conf(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='solrconfig.xml', **kwargs)

    def generate_solr_schema(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='schema.xml', **kwargs)

    def generate_stopwords(self, source, destination, **kwargs):
        self._generate_from_template(source=source, destination=destination,
                                     name='stopwords.txt', **kwargs)

    def create_bin_scripts(self, script, source, destination, **kwargs):
        """ Create a runner for our solr instance """
        if script:
            self._generate_from_template(source=source,
                                         destination=destination,
                                         name=script, executable=True,
                                         **kwargs)

    def copysolr(self, source, destination):
        for sourcedir, dirs, files in os.walk(source):
            relpath = os.path.relpath(sourcedir, source)
            destdir = os.path.join(destination, relpath)

            if os.path.exists(destdir) and not os.path.isdir(destdir):
                shutil.rmtree(destdir)

            if not os.path.exists(destdir):
                os.makedirs(destdir)

            for name in files:
                srcname = os.path.join(sourcedir, name)
                dstname = os.path.join(destdir, name)
                shutil.copy2(srcname, dstname)
                shutil.copystat(srcname, dstname)

    def copy_files(self, src_glob, dst_folder):
        for fname in glob.iglob(src_glob):
            try:
                shutil.copy(fname, dst_folder)
            except IOError as e:
                self.logger.error(e)

    def create_mc_solr(self, path, cores, solr_var):
        """create a empty solr mc dir"""
        shutil.rmtree(os.path.join(path, 'solr'))
        os.makedirs(os.path.join(path, 'solr'))

    def copy_extra_conf(self, extra_conf_files, core=""):
        if extra_conf_files:
            solr_dir = os.path.join(self.install_dir, 'solr')
            conf_dir = os.path.join(solr_dir, core, "conf")
            for i in extra_conf_files:
                #file = os.path.join(self.buildout['buildout']['directory'], i)
                self.copy_files(i, conf_dir)


class SolrSingleRecipe(SolrBase):
    """This recipe builds a single solr index"""

    def __init__(self, buildout, name, options_orig):
        super(SolrSingleRecipe, self).__init__(buildout, name, options_orig)
        self.solropts = self.initSolrOpts(buildout, name, options_orig)

    def install(self):
        """installer"""
        # Copy the instance files
        self.copysolr(os.path.join(self.instanceopts['solr-location'],
                                   'example'), self.install_dir)
        self.copysolr(os.path.join(self.instanceopts['solr-location'], 'dist'),
                      os.path.join(self.install_dir, 'dist'))
        self.copysolr(os.path.join(self.instanceopts['solr-location'],
                                   'contrib'),
                      os.path.join(self.install_dir, 'contrib'))

        self.copy_extra_conf(self.solropts['extra_conf_files'])

        solr_var = self.instanceopts['vardir']
        solr_data = os.path.join(solr_var, 'data')
        if self.instanceopts['logdir']:
            solr_log = self.instanceopts['logdir']
        else:
            solr_log = os.path.join(solr_var, 'log')

        if self.instanceopts['pidpath']:
            solr_pid = self.instanceopts['pidpath']
        else:
            solr_pid = solr_var

        for path in solr_data, solr_log:
            if not os.path.exists(path):
                os.makedirs(path)
        jetty_destination = (self.instanceopts.get('jetty-destination') or
            os.path.join(self.install_dir, 'etc'))
        self.generate_jetty(
            source=(self.instanceopts.get('jetty-template') or
                '%s/jetty.xml.tmpl' % self.tpldir),
            logdir=solr_log,
            serverhost=self.instanceopts['host'],
            serverport=self.instanceopts['port'],
            destination=jetty_destination
        )

        self.generate_log4j(
            source=(self.instanceopts.get('log4j-template') or
                '%s/log4j.properties.tmpl' % self.tpldir),
            destination=jetty_destination,
            logdir=solr_log
        )

        self.generate_logging(
            source=(self.instanceopts.get('logging-template') or
                '%s/logging.properties.tmpl' % self.tpldir),
            destination=jetty_destination,
            logdir=solr_log
        )
        config_template = (self.solropts.get('config-template') or
            '%s/solrconfig.xml.tmpl' % self.tpldir)
        default_config_destination = os.path.join(self.install_dir, 'solr', 'conf')
        if self.is_solr_4():
            default_config_destination = os.path.join(
                self.install_dir, 'solr', 'collection1', 'conf')
        self.generate_solr_conf(
            source=config_template,
            datadir=solr_data,
            destination=(self.solropts['config-destination'] or
                default_config_destination),
            rows=self.solropts['max-num-results'],
            additional_solrconfig=self.solropts['additional-solrconfig'],
            additional_solrconfig_query=self.solropts['additional-solrconfig-query'],
            useColdSearcher=self.solropts.get('useColdSearcher', 'false'),
            maxWarmingSearchers=self.solropts.get('maxWarmingSearchers', '4'),
            requestParsers_multipartUploadLimitInKB=self.solropts[
                'requestParsers-multipartUploadLimitInKB'],
            requestParsers_enableRemoteStreaming=self.solropts[
                'requestParsers-enableRemoteStreaming'],
            autoCommit=self.parseAutoCommit(self.solropts),
            updateLog=self.solropts.get('updateLog', 'false'),
            mergeFactor=self.solropts['mergeFactor'],
            ramBufferSizeMB=self.solropts['ramBufferSizeMB'],
            unlockOnStartup=self.solropts['unlockOnStartup'],
            spellcheckField=self.solropts['spellcheckField'],
            filterCacheSize=self.solropts['filterCacheSize'],
            filterCacheInitialSize=self.solropts['filterCacheInitialSize'],
            filterCacheAutowarmCount=self.solropts['filterCacheAutowarmCount'],
            queryResultCacheSize=self.solropts['queryResultCacheSize'],
            queryResultCacheInitialSize=self.solropts[
                'queryResultCacheInitialSize'],
            queryResultCacheAutowarmCount=self.solropts[
                'queryResultCacheAutowarmCount'],
            documentCacheSize=self.solropts['documentCacheSize'],
            documentCacheInitialSize=self.solropts['documentCacheInitialSize'],
            documentCacheAutowarmCount=self.solropts['documentCacheAutowarmCount'],
            extralibs=self.solropts['extralibs'],
            location=self.install_dir,
            artifact_prefix=self.solropts['artifact_prefix'],
            abortOnConfigurationError=self.solropts['abortOnConfigurationError'],
            directoryFactory=self.solropts['directoryFactory'],
            )

        default_source = '%s/schema.xml.tmpl' % self.tpldir
        source = self.solropts.get('schema-template') or default_source
        self.generate_solr_schema(
            source=source,
            destination=(self.solropts['schema-destination'] or
                default_config_destination),
            analyzers=self.parse_analyzer(self.solropts),
            indeces=self.parse_index(self.solropts),
            options=self.solropts)

        default_source = '%s/stopwords.txt.tmpl' % self.tpldir
        source = self.solropts.get('stopwords-template') or default_source
        self.generate_stopwords(
            source=source,
            destination=(self.solropts['config-destination'] or
                default_config_destination),
            )

        self.create_bin_scripts(
            self.instanceopts.get('script'),
            source='%s/solr-instance.tmpl' % self.tpldir,
            pidfile=os.path.join(solr_pid, 'solr.pid'),
            logfile=os.path.join(solr_log, 'solr.log'),
            destination=self.buildout['buildout']['bin-directory'],
            solrdir=self.install_dir,
            updateurl='http://%s:%s/solr/update' % (
                self.instanceopts['host'],
                self.instanceopts['port']),
            startcmd=self.parse_java_opts(self.instanceopts))

        # returns installed files
        return ()

    def update(self):
        """
        Normally We don't need to do anythin on update -
        install will get called if any of our settings change
        But we allow a workflow for users who wish
        to delete the whole solr-instance folder and
        recreate it with a buildout update. We do this
        often while testing our application.
        """
        if os.path.exists(self.install_dir):
            pass
        else:
            self.install()


class MultiCoreRecipe(SolrBase):
    """Builds a multicore solr without any instances"""

    def __init__(self, buildout, name, options):
        super(MultiCoreRecipe, self).__init__(buildout, name, options)
        if "cores" not in options:
            raise zc.buildout.UserError('Attribute `cores` not defined.')
        try:
            self.cores = [x for x in options["cores"].split() if len(x) > 0]
        except:
            raise zc.buildout.UserError(
                    'Attribute `cores` is not correctly defined. Define as a '
                    'whitespace separated list like `cores = X1 X2 X3`')
        if not self.cores:
            raise zc.buildout.UserError(
                    'Attribute `cores` is not correctly defined. Define as a '
                    'whitespace separated list like `cores = X1 X2 X3`')
        not_allowed_attr = set(self.options_orig.keys()) & NOT_ALLOWED_ATTR

        self.defaultCoreName = options.get('default-core-name', '').strip()

        if len(not_allowed_attr) != 0:
            raise zc.buildout.UserError(
                    'Core attributes are not allowed in multicore recipe')

        #Ensure Buildout tracks changes for configuration regeneration
        for core in self.cores:
            options['core-config-' + core] = str(buildout[core])

    def install(self):
        """installer"""
        # Copy the instance files
        self.copysolr(os.path.join(self.instanceopts['solr-location'],
                                   'example'), self.install_dir)
        self.copysolr(os.path.join(self.instanceopts['solr-location'], 'dist'),
                      os.path.join(self.install_dir, 'dist'))
        self.copysolr(os.path.join(self.instanceopts['solr-location'],
                                   'contrib'),
                      os.path.join(self.install_dir, 'contrib'))

        solr_var = self.instanceopts['vardir']
        if self.instanceopts['logdir']:
            solr_log = self.instanceopts['logdir']
        else:
            solr_log = os.path.join(solr_var, 'log')

        if self.instanceopts['pidpath']:
            solr_pid = self.instanceopts['pidpath']
        else:
            solr_pid = solr_var

        if not os.path.exists(solr_log):
            os.makedirs(solr_log)

        # rm solr example and create a empty one
        self.create_mc_solr(self.install_dir, self.cores, solr_var)

        solr_dir = os.path.join(self.install_dir, 'solr')
        self.generate_solr_mc(
            source='%s/solr.xml.tmpl' % self.tpldir,
            cores=self.cores,
            destination=solr_dir,
            defaultCoreName=self.defaultCoreName)

        #generate defined cores
        for core in self.cores:
            # mghh: We take here the original_options
            #       and merge in the options from every core.
            #       This allows us to define/override options
            #       for all cores.
            options_core = dict(self.options_orig)
            options_core.update(self.buildout[core])
            options_core = self.initSolrOpts(self.buildout, core,
                                             options_core)
            conf_dir = os.path.join(solr_dir, core, "conf")

            if not os.path.exists(conf_dir):
                os.makedirs(conf_dir)

            self.copy_files(os.path.join(self.instanceopts['solr-location'],
                                         'example', 'solr', 'conf', '*.txt'),
                            conf_dir)

            solr_data = os.path.join(solr_var, 'data', core)
            if not os.path.exists(solr_data):
                os.makedirs(solr_data)
            config_template = (options_core.get('config-template') or
                '%s/solrconfig.xml.tmpl' % self.tpldir)

            self.generate_solr_conf(
                source=config_template,
                datadir=solr_data,
                destination=conf_dir,
                rows=options_core['max-num-results'],
                additional_solrconfig=options_core['additional-solrconfig'],
                additional_solrconfig_query=options_core['additional-solrconfig-query'],
                useColdSearcher=options_core.get('useColdSearcher', 'false'),
                maxWarmingSearchers=options_core.get('maxWarmingSearchers',
                                                     '4'),
                requestParsers_multipartUploadLimitInKB=options_core[
                    'requestParsers-multipartUploadLimitInKB'],
                requestParsers_enableRemoteStreaming=options_core[
                    'requestParsers-enableRemoteStreaming'],
                autoCommit=self.parseAutoCommit(options_core),
                updateLog=options_core['updateLog'],
                mergeFactor=options_core['mergeFactor'],
                ramBufferSizeMB=options_core['ramBufferSizeMB'],
                unlockOnStartup=options_core['unlockOnStartup'],
                spellcheckField=options_core['spellcheckField'],
                filterCacheSize=options_core['filterCacheSize'],
                filterCacheInitialSize=options_core['filterCacheInitialSize'],
                filterCacheAutowarmCount=options_core[
                    'filterCacheAutowarmCount'],
                queryResultCacheSize=options_core['queryResultCacheSize'],
                queryResultCacheInitialSize=options_core[
                    'queryResultCacheInitialSize'],
                queryResultCacheAutowarmCount=options_core[
                    'queryResultCacheAutowarmCount'],
                documentCacheSize=options_core['documentCacheSize'],
                documentCacheInitialSize=options_core[
                    'documentCacheInitialSize'],
                documentCacheAutowarmCount=options_core['documentCacheAutowarmCount'],
                extralibs=options_core['extralibs'],
                location=self.install_dir,
                artifact_prefix=options_core['artifact_prefix'],
                abortOnConfigurationError=options_core['abortOnConfigurationError'],
                directoryFactory=options_core['directoryFactory'],
                )

            default_source = '%s/stopwords.txt.tmpl' % self.tpldir
            source = options_core.get('stopwords-template') or default_source
            self.generate_stopwords(
                source=source,
                destination=conf_dir,
                )

            default_source = '%s/schema.xml.tmpl' % self.tpldir
            source = options_core.get('schema-template') or default_source
            self.generate_solr_schema(
                source=source,
                destination=conf_dir,
                analyzers=self.parse_analyzer(options_core),
                indeces=self.parse_index(options_core),
                options=options_core)

            self.copy_extra_conf(options_core['extra_conf_files'], core=core)

        jetty_destination = (self.instanceopts.get('jetty-destination') or
            os.path.join(self.install_dir, 'etc'))

        self.generate_jetty(
            source=(self.instanceopts.get('jetty-template') or
                '%s/jetty.xml.tmpl' % self.tpldir),
            logdir=solr_log,
            serverhost=self.instanceopts['host'],
            serverport=self.instanceopts['port'],
            destination=jetty_destination)

        self.generate_log4j(
            source=(self.instanceopts.get('log4j-template') or
                '%s/log4j.properties.tmpl' % self.tpldir),
            destination=jetty_destination,
            logdir=solr_log
        )

        self.generate_logging(
            source=(self.instanceopts.get('logging-template') or
                '%s/logging.properties.tmpl' % self.tpldir),
            destination=jetty_destination,
            logdir=solr_log
        )

        self.create_bin_scripts(
            self.instanceopts.get('script'),
            source='%s/solr-instance.tmpl' % self.tpldir,
            pidfile=os.path.join(solr_pid, 'solr.pid'),
            logfile=os.path.join(solr_log, 'solr.log'),
            destination=self.buildout['buildout']['bin-directory'],
            solrdir=self.install_dir,
            updateurl='http://%s:%s/solr/update' % (
                self.instanceopts['host'],
                self.instanceopts['port']),
            startcmd=self.parse_java_opts(self.instanceopts))

        return ()

    def update(self):
        """
        Normally We don't need to do anythin on update -
        install will get called if any of our settings change
        But we allow a workflow for users who wish
        to delete the whole solr-instance folder and
        recreate it with a buildout update. We do this
        often while testing our application.
        """
        if os.path.exists(self.install_dir):
            pass
        else:
            self.install()
