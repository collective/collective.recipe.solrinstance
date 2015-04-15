# -*- coding: utf-8 -*-
from genshi.template import Context
from genshi.template import NewTextTemplate
from genshi.template.base import TemplateSyntaxError
from genshi.template.eval import UndefinedError
from hexagonit.recipe.download import Recipe as DownloadRecipe
from hexagonit.recipe.download import TRUE_VALUES
import glob
import logging
import os
import shutil
import sys
import zc.buildout

DEFAULT_DOWNLOAD_URLS = {
    5: 'http://archive.apache.org/dist/lucene/solr/5.1.0/solr-5.1.0.tgz',
    4: 'http://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz',
    3: 'http://archive.apache.org/dist/lucene/solr/3.6.2/apache-solr-3.6.2.tgz'
}

ZOPE_CONF = """
<product-config {section-name:s}>
    address {host:s}:{port:s}
    basepath {basepath:s}
</product-config>
"""

INDEX_TYPES = set([
    'text', 'text_ws', 'ignored', 'date', 'string',
    'boolean', 'int', 'integer', 'long', 'float', 'double'
])

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
"""  # noqa

DEFAULT_CHAR_FILTERS = """
"""

DEFAULT_TOKENIZER = """
    text solr.ICUTokenizerFactory
    text_ws solr.WhitespaceTokenizerFactory
"""

ALLOWED_OPERATORS = ('OR', 'AND')

#: Processors that allow just one entry per field type
UNIQUE_PROCESSORS = ('tokenizer',)


NOT_ALLOWED_ATTR = set([
    'index', 'filter', 'unique-key', 'max-num-results', 'default-search-field',
    'default-operator', 'additional-solrconfig', 'additional-solrconfig-query',
    'autoCommitMaxDocs', 'autoCommitMaxTime', 'updateLog',
    'requestParsers-multipartUploadLimitInKB',
    'requestParsers-enableRemoteStreaming',
])


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


class MultiCoreSolrRecipe(object):
    """Generates a Solr setup with multiple cores
    """

    def __init__(self, buildout, name, options):
        self.name = name
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)
        self.options = options
        self.options_orig = options.copy()

        # Set default values for options
        self.options['location'] = self.install_dir

        # BBB
        if 'solr-location' not in self.options:
            self.options['solr-location'] = self.solr_autoinstall()

        # only strings are allowed in UserDict types.
        self.options['customTemplate'] = \
            str('schema-template' in self.options_orig).lower()

        # Shorten some methods
        sd = self.options.setdefault
        join = os.path.join

        sd('section-name', self.name)
        sd('host', 'localhost')
        sd('port', '8983')

        # Base configuration, base_dir is solr core root and will be
        # overwritten in multicore recipe for each core.
        options['basedir'] = join(self.install_dir, 'solr')
        sd('vardir', join(self.buildout['buildout']['directory'], 'var'))
        sd('pidpath', join(options['vardir'], 'solr'))
        sd('logdir', join(options['vardir'], 'log'))
        sd('datadir', join(options['vardir'], 'solr', 'data'))
        sd('java_opts', '')
        sd('basepath', '/solr')
        sd('zope-conf', ZOPE_CONF.format(**options))

        # jetty
        sd('jetty-destination', join(self.install_dir, 'etc'))
        sd('jetty-template', join(self.template_dir, 'jetty.xml.tmpl'))

        # log4j
        sd('log4j-template', os.path.realpath(join(
            self.template_dir, '..', 'log4j.properties.tmpl')))
        sd('logging-template', os.path.realpath(join(
            self.template_dir, '..', 'logging.properties.tmpl')))

        # Config
        conf_dir = join(options['basedir'], 'conf')
        sd('config-destination', conf_dir)
        sd('config-template', join(self.template_dir, 'solrconfig.xml.tmpl'))

        # Schema
        sd('schema-template', join(self.template_dir, 'schema.xml.tmpl'))
        sd('schema-destination', conf_dir)

        # Stopwords
        sd('stopwords-template', os.path.realpath(join(
            self.template_dir, '..', 'stopwords.txt.tmpl')))

        # Synonyms
        sd('synonyms-template', os.path.realpath(join(
            self.template_dir, '..', 'synonyms.txt.tmpl')))

        # Solr defaults
        sd('max-num-results', '500')
        sd('abortOnConfigurationError', 'false')
        sd('additional-schema-config', '')
        sd('additional-solrconfig', '')
        sd('additional-solrconfig-query', '')
        sd('additionalFieldConfig', '')
        sd('autoCommitMaxDocs', '')
        sd('autoCommitMaxTime', '')
        sd('char-filter', DEFAULT_CHAR_FILTERS)
        sd('default-core-name', '')
        sd('default-operator', 'OR')
        sd('default-search-field', '')
        sd('directoryFactory', 'solr.NRTCachingDirectoryFactory')
        sd('documentCacheAutowarmCount', '0')
        sd('documentCacheInitialSize', '512')
        sd('documentCacheSize', '512')
        sd('filter', DEFAULT_FILTERS)
        sd('extra-field-types', '')
        sd('extra-conf-files', '')
        sd('filterCacheAutowarmCount', '4096')
        sd('filterCacheInitialSize', '4096')
        sd('filterCacheSize', '16384')
        sd('maxWarmingSearchers', '4')
        sd('mergeFactor', '10')
        sd('queryResultCacheAutowarmCount', '32')
        sd('queryResultCacheInitialSize', '64')
        sd('queryResultCacheSize', '128')
        sd('ramBufferSizeMB', '16')
        sd('requestParsers-enableRemoteStreaming', 'false')
        sd('requestParsers-multipartUploadLimitInKB', '102400')
        sd('script', 'solr-instance')
        sd('spellcheckField', 'default')
        sd('tokenizer', DEFAULT_TOKENIZER)
        sd('unique-key', 'uid')
        sd('unlockOnStartup', 'true')
        sd('updateLog', 'false')
        sd('useColdSearcher', 'true')

        self._finalize_options(options, self.options)

    def _finalize_options(self, source, target):
        # strip whitespaces
        for k, v in source.items():
            target[k] = v.strip()

        # see self.extralibs property
        target.pop('extralibs', None)

        self.validate_options(target)

    @property
    def solr_version(self):
        return int(self.options['solr-version'])

    @property
    def install_dir(self):
        return os.path.join(
            self.buildout['buildout']['parts-directory'], self.name)

    @property
    def template_dir(self):
        return os.path.join(
            os.path.dirname(__file__), 'templates', str(self.solr_version))

    @property
    def instance_dir(self):
        if self.solr_version < 5:
            return os.path.join(self.options['solr-location'], 'example')

        return os.path.join(self.options['solr-location'], 'server')

    @property
    def sample_conf_dir(self):
        base = os.path.join(self.instance_dir, 'solr')
        if self.solr_version < 4:
            return os.path.join(base, 'conf')
        elif self.solr_version == 4:
            return os.path.join(base, 'collection1', 'conf')

        return os.path.join(base, 'configsets', 'basic_configs', 'conf')

    def solr_autoinstall(self):
        if self.solr_version not in DEFAULT_DOWNLOAD_URLS:
            raise zc.buildout.UserError(
                'Solr {0:d}.x is not supported.'.format(self.solr_version))

        name = '{0:s}-download'.format(self.name)
        directory = os.path.join(
            self.buildout['buildout']['parts-directory'], name)

        if not os.path.exists(directory):
            DownloadRecipe(self.buildout, name, {
                'url': DEFAULT_DOWNLOAD_URLS[self.solr_version],
                'strip-top-level-dir': 'true',
                'destination': directory,
            }).install()

        return directory

    @property
    def extralibs(self):
        extralibs = []
        option_extralibs = self.options_orig.get('extralibs', '').strip()
        for lib in option_extralibs.splitlines():
            if ':' in lib:
                path, regex = lib.split(':', 1)
            else:
                path = lib
                regex = ".*\.jar"
            if path.strip():
                extralibs.append({'path': path, 'regex': regex})

        return extralibs

    def copy_solr(self, source, destination):
        for sourcedir, dirs, files in os.walk(source):
            relpath = os.path.relpath(sourcedir, source)
            destdir = os.path.join(destination, relpath)

            if os.path.exists(destdir) and not os.path.isdir(destdir):
                shutil.rmtree(destdir)

            make_dirs(destdir)

            for name in files:
                srcname = os.path.join(sourcedir, name)
                dstname = os.path.join(destdir, name)
                shutil.copy2(srcname, dstname)
                shutil.copystat(srcname, dstname)

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
            raise zc.buildout.UserError(
                'Error in template {0:s}:\n{1:s}'.format(name, e.msg))

        if executable:
            output = '#!{0:s}\n{1:s}'.format(sys.executable, output)

        if executable and sys.platform == 'win32':
            from pkg_resources import resource_string
            exe = output_file + '.exe'
            open(exe, 'wb').write(resource_string('setuptools', 'cli.exe'))
            output_file = output_file + '-script.py'

        with open(output_file, 'wb') as outfile:
            outfile.write(output.encode('utf8'))

        if executable:
            self.logger.info('Generated script %r.', name)
            try:
                os.chmod(output_file, 493)  # 0755 / 0o755
            except (AttributeError, os.error):
                pass
        else:
            self.logger.info('Generated file %r.', name)

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
                    raise zc.buildout.UserError(
                        'Invalid index type: {0:s}'.format(index))

                filter = {'class': klass, 'extra': extra}
                if unique:
                    filters[index] = [filter]
                else:
                    filters[index].append(filter)
        return filters

    def get_analyzers(self, options):
        """Parse all analyzers and their configuration from the options."""
        analyzers = {}
        for analyzer_type in ('query', 'index'):
            analyzers[analyzer_type] = {
                'filter': options['filter'],
                'char_filter': options['char-filter'],
                'tokenizer': options['tokenizer']
            }

            for proc in ('filter', 'char-filter', 'tokenizer'):
                # Options are stored like 'filter-query' and 'filter-index'
                processor = '{0}-{1}'.format(proc, analyzer_type)
                proc_store = proc.replace('-', '_')
                analyzers[analyzer_type][proc_store] += '\n {0:s}'.format(
                    options.get(processor, '').strip())

            for processor in analyzers[analyzer_type]:
                unique = processor in UNIQUE_PROCESSORS
                analyzers[analyzer_type][processor] = \
                    self.parse_processor(analyzers[analyzer_type][processor],
                                         unique=unique)
        return analyzers

    @property
    def java_opts(self):
        """Parsed the java opts from `options`. """
        _start = ['java', '-jar']
        _jar = 'start.jar'
        if not self.options['java_opts']:
            cmd_opts = _start
        else:
            _opts = self.options['java_opts'].splitlines()
            cmd_opts = _start + _opts
        cmd_opts.append(_jar)
        return cmd_opts

    def _split_index_line(self, line):
        # Split an index line.
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

    def get_indexes(self, options):
        """Parses the index definitions from the options."""
        indexAttrs = set(INDEX_ATTRIBUTES.keys())
        indeces = []
        names = []
        for line in options['index'].strip().splitlines():
            if line.strip().startswith('#'):
                continue  # Allow comments
            entry = {}
            for item in self._split_index_line(line):
                if item.count(':') > 1:
                    pos = item.find(':')
                    attr = item[:pos]
                    value = item[pos+1:]
                else:
                    attr, value = item.split(':')[:2]
                if attr == 'copyfield':
                    entry.setdefault(attr, []).append(value)
                else:
                    entry[attr] = value

            keys = set(entry.keys())
            if not keys.issubset(indexAttrs):
                if options.get('customTemplate', 'false') in TRUE_VALUES:
                    extras = []
                    for key in sorted(keys.difference(indexAttrs)):
                        extras.append('{0:s}="{1:s}"'.format(key, entry[key]))
                    entry['extras'] = ' '.join(extras)
                else:
                    invalid = keys.difference(indexAttrs)
                    raise zc.buildout.UserError(
                        'Invalid index attribute(s): {0:s}. Allowed '
                        'attributes are: {1:s}.'.format(', '.join(invalid),
                                                        ', '.join(indexAttrs))
                    )

            if entry['name'] in names:
                raise zc.buildout.UserError(
                    'Duplicate name error: "{0:s}" already defined.'.format(
                        entry['name']))

            names.append(entry['name'])

            for key in INDEX_ATTRIBUTES:
                value = entry.get(key, INDEX_ATTRIBUTES[key])

                if key == 'copyfield':
                    entry[key] = [{'source': entry['name'], 'dest':val}
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

        unique = options['unique-key']
        if unique and unique not in names:
            raise zc.buildout.UserError(
                'Unique key without matching index: {0:s}'.format(unique))

        if unique and not \
           indeces[names.index(unique)].get('required', None) == 'true' and \
           indeces[names.index(unique)].get('default', '') == '':
            raise zc.buildout.UserError(
                'Unique key needs to declared "required"=true or '
                '"default"=NEW: {0:s}'.format(unique))

        default = options['default-search-field']
        if default and default not in names:
            raise zc.buildout.UserError(
                'Default search field without matching index: '
                '{0:s}'.format(default))

        return indeces

    @property
    def auto_commit(self):
        mdocs = self.options['autoCommitMaxDocs']
        mtime = self.options['autoCommitMaxTime']
        if mdocs or mtime:
            result = ['<autoCommit>']
            if mdocs:
                result.append('<maxDocs>{0:s}</maxDocs>'.format(str(mdocs)))
            if mtime:
                result.append('<maxTime>{0:s}</maxTime>'.format(str(mtime)))
            result.append('</autoCommit>')
            return '\n'.join(result)
        return ''

    @property
    def artifact_prefix(self):
        test_artifacts = os.path.join(
            self.options['solr-location'], 'dist', 'apache-*')
        if self.solr_version < 4 or glob.glob(test_artifacts):
            return 'apache-'
        return ''

    def copy_files(self, src_glob, dst_folder):
        for fname in glob.iglob(src_glob):
            try:
                shutil.copy(fname, dst_folder)
            except IOError as e:
                self.logger.error(
                    'Could not copy {0:s} to {1:s}: {2:s}'.format(
                        fname, dst_folder, e))

    def copy_extra_conf(self, options):
        extra_conf_files = options['extra-conf-files'].splitlines()
        if not extra_conf_files:
            return
        for conf_file in extra_conf_files:
            self.copy_files(conf_file, options['config-destination'])

    def validate_options(self, options):
        # Solr 5 accepts OR|AND only

        if options['default-operator'] not in ALLOWED_OPERATORS:
            raise zc.buildout.UserError(
                'Only one of {0:s} allowed as default-operator.'.format(
                    ALLOWED_OPERATORS))

        try:
            assert int(options['max-num-results']) > 1
        except (AssertionError, TypeError, ValueError):
            raise zc.buildout.UserError(
                'Please use a positive integer as max-num-results.')

    @property
    def cores(self):
        cores = []
        for core in self.options['cores'].split():
            if core in cores:
                raise zc.buildout.UserError(
                    'Core %r was already defined.' % core)

            cores.append(core.strip())

        if not cores:
            raise zc.buildout.UserError(
                'Attribute `cores` is not correctly defined. Define as a '
                'whitespace or line separated list like `cores = X1 X2 X3`'
            )

        return cores

    def install_base(self):
        """Generic installer for single and multi core setups"""

        # First wipe instance
        # if os.path.exists(self.install_dir):
        #     shutil.rmtree(self.install_dir)

        # Create directories if they don't exist
        make_dirs(self.options['vardir'])
        make_dirs(self.options['logdir'])
        make_dirs(self.options['datadir'])
        make_dirs(self.options['pidpath'])

        # Copy the instance files
        self.copy_solr(
            self.instance_dir,
            self.install_dir
        )

        if self.cores:
            shutil.rmtree(self.options['basedir'])
            os.makedirs(self.options['basedir'])

        self.copy_solr(
            os.path.join(self.options['solr-location'], 'dist'),
            os.path.join(self.install_dir, 'dist')
        )
        self.copy_solr(
            os.path.join(self.options['solr-location'], 'contrib'),
            os.path.join(self.install_dir, 'contrib')
        )

        # Jetty
        self._generate_from_template(
            destination=self.options['jetty-destination'],
            name='jetty.xml',
            serverhost=self.options['host'],  # BBB use host in jetty.xml.tpl
            serverport=self.options['port'],  # BBB use port in jetty.xml.tpl
            source=self.options['jetty-template'],
            **self.options
        )

        # Log4j
        self._generate_from_template(
            destination=self.options['jetty-destination'],
            name='log4j.properties',
            source=self.options['log4j-template'],
            **self.options
        )
        self._generate_from_template(
            destination=self.options['jetty-destination'],
            name='logging.properties',
            source=self.options['logging-template'],
            **self.options
        )

        # Startup script
        if self.options['script']:
            self._generate_from_template(
                destination=self.buildout['buildout']['bin-directory'],
                executable=True,
                logfile=os.path.join(self.options['logdir'], 'solr.log'),
                name=self.options['script'],
                pidfile=os.path.join(self.options['pidpath'], 'solr.pid'),
                solrdir=self.install_dir,
                source=os.path.join(self.template_dir, 'solr-instance.tmpl'),
                updateurl='http://{0:s}:{1:s}/solr/update'.format(
                    self.options['host'],
                    self.options['port']
                ),
                startcmd=self.java_opts,
                **self.options
            )

    def install_core(self, name, options):

        self.validate_options(options)
        self.logger.name = name

        # Create directories
        make_dirs(options['basedir'])
        make_dirs(options['config-destination'])
        make_dirs(options['datadir'])

        # Copy solr sampledata provided in sample_core
        self.copy_solr(self.sample_conf_dir, options['config-destination'])

        # BBB: Support old customized schema.xml, solrconfig.xml files by
        # providing information to genshi templates on options.options
        # variable.
        legacy_options = self.options.copy()
        legacy_options['additionalSchemaConfig'] = options[
            'additional-schema-config']
        legacy_options['name'] = name
        legacy_options['defaultOperator'] = options['default-operator']
        legacy_options['extraFieldTypes'] = options['extra-field-types']
        legacy_options['uniqueKey'] = options['unique-key']
        legacy_options['defaultSearchField'] = options[
            'default-search-field']

        # Config
        self._generate_from_template(
            additional_solrconfig=options['additional-solrconfig'],
            additional_solrconfig_query=options[
                'additional-solrconfig-query'],
            artifact_prefix=self.artifact_prefix,
            autoCommit=self.auto_commit,
            defaultSearchField=options['default-search-field'],
            destination=options['config-destination'],
            extralibs=self.extralibs,
            name='solrconfig.xml',
            requestParsers_enableRemoteStreaming=options[
                'requestParsers-enableRemoteStreaming'],
            requestParsers_multipartUploadLimitInKB=options[
                'requestParsers-multipartUploadLimitInKB'],
            rows=options['max-num-results'],
            source=options['config-template'],
            uniqueKey=options['unique-key'],
            **options
        )

        # Schema
        self._generate_from_template(
            additionalSchemaConfig=options['additional-schema-config'],
            analyzers=self.get_analyzers(options),
            defaultOperator=options['default-operator'],
            defaultSearchField=options['default-search-field'],
            destination=options['schema-destination'],
            extraFieldTypes=options['extra-field-types'],
            indeces=self.get_indexes(options),
            name='schema.xml',
            options=legacy_options,  # BBB
            source=options['schema-template'],
            uniqueKey=options['unique-key'],
            **options
        )

        # Stopwords
        self._generate_from_template(
            destination=options['config-destination'],
            name='stopwords.txt',
            source=options['stopwords-template']
        )

        # Synonyms
        self._generate_from_template(
            destination=options['config-destination'],
            name='synonyms.txt',
            source=options['synonyms-template']
        )

        # This may also contain a stopwords.txt & synonyms.txt
        # file which overwrites the ones created above.
        self.copy_extra_conf(options)
        self.copy_files(
            os.path.join(self.instance_dir, 'solr', 'conf', '*.txt'),
            options['config-destination']
        )

        # New style core.properties file, see:
        # https://cwiki.apache.org/confluence/display/solr/Defining+core.properties
        if self.solr_version > 4:
            self._generate_from_template(
                corename=name,
                destination=options['basedir'],
                name='core.properties',
                source=os.path.join(self.template_dir, 'core.properties.tmpl'),
                **options
            )

    def install(self):
        # Run generic install
        self.install_base()

        solr_dir = os.path.join(self.install_dir, 'solr')
        self._generate_from_template(
            defaultCoreName=self.options['default-core-name'],
            destination=solr_dir,
            source=os.path.join(self.template_dir, 'solr.xml.tmpl'),
            name='solr.xml',
            cores=self.cores,
            host=self.options['host'],
            port=self.options['port']
        )

        # Generate defined cores
        for core in self.cores:
            core_dir = os.path.join(solr_dir, core)
            conf_dir = os.path.join(core_dir, 'conf')
            data_dir = os.path.join(self.options['datadir'], core)

            # We take here the original_options and merge in the options
            # from every core. This allows us to define/override options
            # for all cores.
            options_core = self.options.copy()

            # options_core.update(self.buildout[core])
            # ... does not strip whitespaces from core buildout attributes
            self._finalize_options(self.buildout.get(core, {}), options_core)

            options_core['basedir'] = core_dir
            options_core['datadir'] = data_dir
            options_core['config-destination'] = conf_dir
            options_core['schema-destination'] = conf_dir

            self.install_core(core, options_core)

        return (self.options['location'], )

    def update(self):
        """
        Normally We don't need to do anythin on update -
        install will get called if any of our settings change
        But we allow a workflow for users who wish
        to delete the whole solr-instance folder and
        recreate it with a buildout update. We do this
        often while testing our application.
        """
        if not os.path.exists(self.install_dir):
            return self.install()


class SingleCoreSolrRecipe(MultiCoreSolrRecipe):
    """Builds a single core solr setup - DEPRECATED"""

    # This collection1 demo core is used by solr 4 only.
    cores = ['collection1', ]

    def install(self):
        if self.solr_version < 4:
            self.install_base()
            self.install_core(self.name, self.options)
            return (self.options['location'], )

        if self.solr_version == 4:
            return super(SingleCoreSolrRecipe, self).install()

        raise zc.buildout.UserError(
            'Solr {0} no longer supports deprecated single core setups. '
            'Please use a multicore setup with one core.'.format(
                self.solr_version))
