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
import pkg_resources
import shutil
import sys
import zc.buildout
import re

DEFAULT_DOWNLOAD_URLS = {
    5: 'http://archive.apache.org/dist/lucene/solr/5.0.0/solr-5.0.0.tgz',
    4: 'http://archive.apache.org/dist/lucene/solr/4.10.3/solr-4.10.3.tgz',
    3: 'http://archive.apache.org/dist/lucene/solr/3.6.2/apache-solr-3.6.2.tgz'
}

ZOPE_CONF = """
<product-config {section-name:s}>
    address {host:s}:{port:s}
    basepath {basepath:s}
</product-config>
"""

INDEX_TYPES = {
    'text', 'text_ws', 'ignored', 'date', 'string',
    'boolean', 'integer', 'long', 'float', 'double'
}

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

#: Processors that allow just one entry per field type
UNIQUE_PROCESSORS = ('tokenizer',)


NOT_ALLOWED_ATTR = {
    'index', 'filter', 'unique-key', 'max-num-results', 'default-search-field',
    'default-operator', 'additional-solrconfig', 'additional-solrconfig-query',
    'autoCommitMaxDocs', 'autoCommitMaxTime', 'updateLog',
    'requestParsers-multipartUploadLimitInKB',
    'requestParsers-enableRemoteStreaming',
}


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


class SolrBase(object):
    """This class hold every base functions """

    def __init__(self, buildout, name, options):
        self.name = name
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)

        self.options_orig = options
        self.options_orig['location'] = self.install_dir

    @property
    def solr_version(self):
        return int(self.options_orig['solr-version'])

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

    def solr_autoinstall(self):
        if self.solr_version not in DEFAULT_DOWNLOAD_URLS:
            raise zc.buildout.UserError(
                'Solr {0:d}.x is not supported.'.format(self.solr_version))

        name = '{0:s}-download'.format(self.name)
        directory = os.path.join(
            self.buildout['buildout']['parts-directory'], name)

        if os.path.exists(directory):
            shutil.rmtree(directory)

        DownloadRecipe(self.buildout, name, {
            'url': DEFAULT_DOWNLOAD_URLS[self.solr_version],
            'strip-top-level-dir': 'true',
            'destination': directory,
        }).install()

        return directory

    @property
    def options(self):
        options = self.options_orig

        # BBB
        if 'solr-location' not in self.options_orig:
            options.setdefault('solr-location', self.solr_autoinstall())

        options.setdefault('section-name', self.name)
        options.setdefault('host', 'localhost')
        options.setdefault('port', '8983')

        # Base configuration, base_dir is solr core root and will be
        # overwritten in multicore recipe for each core.
        options['basedir'] = os.path.join(self.install_dir, 'solr')

        var_dir = os.path.join(self.buildout['buildout']['directory'], 'var')
        options.setdefault('vardir', os.path.join(var_dir, 'solr'))
        options.setdefault('pidpath', os.path.join(var_dir, 'solr'))
        options.setdefault('datadir', os.path.join(var_dir, 'solr', 'data'))
        options.setdefault('logdir', os.path.join(var_dir, 'log'))
        options.setdefault('java_opts', '')
        options.setdefault('basepath', '/solr')
        options.setdefault('zope-conf', ZOPE_CONF.format(**options))

        # jetty
        options.setdefault('jetty-destination', os.path.join(
            self.install_dir, 'etc'))
        options.setdefault('jetty-template', os.path.join(
            self.template_dir, 'jetty.xml.tmpl'))
        options.setdefault('jetty-destination', os.path.join(
            self.install_dir, 'etc'))

        # log4j
        options.setdefault('log4j-template', os.path.realpath(os.path.join(
            self.template_dir, '..', 'log4j.properties.tmpl')))
        options.setdefault('logging-template', os.path.realpath(os.path.join(
            self.template_dir, '..', 'logging.properties.tmpl')))

        # Config
        conf_dir = os.path.join(options['basedir'], 'conf')
        options.setdefault('config-destination', conf_dir)
        options.setdefault('config-template', os.path.join(
            self.template_dir, 'solrconfig.xml.tmpl'))

        # Schema
        options.setdefault('schema-template', os.path.join(
            self.template_dir, 'schema.xml.tmpl'))
        options.setdefault('schema-destination', conf_dir)

        # Stopwords
        options.setdefault('stopwords-template', os.path.realpath(os.path.join(
            self.template_dir, '..', 'stopwords.txt.tmpl')))

        # Solr defaults
        options.setdefault('max-num-results', '500')
        try:
            assert int(options['max-num-results']) > 1
        except (AssertionError, TypeError, ValueError):
            raise zc.buildout.UserError('Please use a positive integer for '
                                        'the number of default results')

        options.setdefault('abortOnConfigurationError', 'false')
        options.setdefault('additional-schema-config', '')
        options.setdefault('additional-solrconfig', '')
        options.setdefault('additional-solrconfig-query', '')
        options.setdefault('additionalFieldConfig', '')
        options.setdefault('autoCommitMaxDocs', '')
        options.setdefault('autoCommitMaxTime', '')
        options.setdefault('char-filter', DEFAULT_CHAR_FILTERS)
        options.setdefault('default-core-name', '')
        options.setdefault('default-operator', 'OR')
        options.setdefault('default-search-field', '')
        options.setdefault('directoryFactory',
                           'solr.NRTCachingDirectoryFactory')
        options.setdefault('documentCacheAutowarmCount', '0')
        options.setdefault('documentCacheInitialSize', '512')
        options.setdefault('documentCacheSize', '512')
        options.setdefault('filter', DEFAULT_FILTERS)
        options.setdefault('extra-field-types', '')
        options.setdefault('extra-conf-files', '')
        options.setdefault('filterCacheAutowarmCount', '4096')
        options.setdefault('filterCacheInitialSize', '4096')
        options.setdefault('filterCacheSize', '16384')
        options.setdefault('maxWarmingSearchers', '4')
        options.setdefault('mergeFactor', '10')
        options.setdefault('queryResultCacheAutowarmCount', '32')
        options.setdefault('queryResultCacheInitialSize', '64')
        options.setdefault('queryResultCacheSize', '128')
        options.setdefault('ramBufferSizeMB', '16')
        options.setdefault('requestParsers-enableRemoteStreaming', 'false')
        options.setdefault('requestParsers-multipartUploadLimitInKB', '102400')
        options.setdefault('script', 'solr-instance')
        options.setdefault('spellcheckField', 'default')
        options.setdefault('tokenizer', DEFAULT_TOKENIZER)
        options.setdefault('unique-key', 'uid')
        options.setdefault('unlockOnStartup', 'true')
        options.setdefault('updateLog', 'false')
        options.setdefault('useColdSearcher', 'true')

        options.pop('extralibs', None)

        # strip whitespaces
        for k, v in options.items():
            options[k] = v.strip()

        return options

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
            exe = output_file + '.exe'
            open(exe, 'wb').write(
                pkg_resources.resource_string('setuptools', 'cli.exe')
            )
            self.generated.append(exe)
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

    @property
    def analyzer(self):
        """Parse all analyzers and their configuration from the options."""
        analyzers = {}
        for analyzer_type in ('query', 'index'):
            analyzers[analyzer_type] = {
                'filter': self.options['filter'],
                'char_filter': self.options['char-filter'],
                'tokenizer': self.options['tokenizer']
            }

            for proc in ('filter', 'char-filter', 'tokenizer'):
                # Options are stored like 'filter-query' and 'filter-index'
                processor = '{0}-{1}'.format(proc, analyzer_type)
                proc_store = proc.replace('-', '_')
                analyzers[analyzer_type][proc_store] += '\n {0:s}'.format(
                    self.options.get(processor, '').strip())

            for processor in analyzers[analyzer_type]:
                unique = processor in UNIQUE_PROCESSORS
                analyzers[analyzer_type][processor] = \
                    self.parse_processor(analyzers[analyzer_type][processor],
                                         unique=unique)
        return analyzers

    @property
    def java_opts(self):
        """Parsed the java opts from `options`. """
        cmd_opts = []
        _start = ['java', '-jar']
        _jar = 'start.jar'
        _opts = []
        if not self.options['java_opts']:
            cmd_opts = _start
        else:
            _opts = self.options['java_opts'].splitlines()
            cmd_opts = _start + _opts
        cmd_opts.append(_jar)
        return cmd_opts

    def get_indexes(self, options):
        """Parses the index definitions from the options."""
        indexAttrs = set(INDEX_ATTRIBUTES.keys())
        indeces = []
        names = []
        for line in options.get('index', '').strip().splitlines():
            if line.strip().startswith('#'):
                continue  # Allow comments
            entry = {}
            for attr, value in re.findall(r'([^:\s]+):([^:\s]+)\s?', line):
                if attr == 'copyfield':
                    entry.setdefault(attr, []).append(value)
                else:
                    entry[attr] = value

            keys = set(entry.keys())
            if not keys.issubset(indexAttrs):
                if options.get('customTemplate'):
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

    def install_base(self):
        """Generic installer for single and multi core setups"""

        # First wipe instance
        if os.path.exists(self.instance_dir):
            shutil.rmtree(self.install_dir)

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


class SolrSingleRecipe(SolrBase):
    """This recipe builds a single solr index"""

    cores = set()

    def install_core(self, name, options):

        # Create directories
        make_dirs(options['basedir'])
        make_dirs(options['config-destination'])
        make_dirs(options['datadir'])

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
            analyzers=self.analyzer,
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

        # This may also contain a stopwords.txt file which overwrites the one
        # created above.
        self.copy_extra_conf(options)

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

        # Install a single solr core
        self.install_core(self.name, self.options)

        return ()


class MultiCoreRecipe(SolrSingleRecipe):
    """Builds a multicore solr without any instances"""

    @property
    def cores(self):
        cores = set()
        for core in self.options.get('cores', '').splitlines():
            cores.add(core.strip())

        if not cores:
            raise zc.buildout.UserError(
                'Attribute `cores` is not correctly defined. Define as a '
                'whitespace separated list like `cores = X1 X2 X3`'
            )

        return cores

    def install(self):
        # Run generic install
        self.install_base()

        # Build core document
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

            # XXX: We take here the original_options and merge in the options
            #      from every core. This allows us to define/override options
            #      for all cores.
            options_core = self.options.copy()

            # options_core.update(self.buildout[core])
            # ... does not strip whitespaces from core buildout attributes
            for k, v in self.buildout[core].items():
                options_core[k] = v.strip()

            options_core['basedir'] = core_dir
            options_core['datadir'] = data_dir
            options_core['config-destination'] = conf_dir
            options_core['schema-destination'] = conf_dir

            self.install_core(core, options_core)

        return ()

    # def update(self):
    #     """
    #     Normally We don't need to do anythin on update -
    #     install will get called if any of our settings change
    #     But we allow a workflow for users who wish
    #     to delete the whole solr-instance folder and
    #     recreate it with a buildout update. We do this
    #     often while testing our application.
    #     """
    #     if os.path.exists(self.install_dir):
    #         pass
    #     else:
    #         self.install()
