def __init__(self, params=None, auto_init=True):
        """Create a FileDownloader object with the given options.
        @param auto_init    Whether to load the default extractors and print header (if verbose).
                            Set to 'no_verbose_header' to not print the header
        """
        if params is None:
            params = {}
        self.params = params
        self._ies = {}
        self._ies_instances = {}
        self._pps = {k: [] for k in POSTPROCESS_WHEN}
        self._printed_messages = set()
        self._first_webpage_request = True
        self._post_hooks = []
        self._close_hooks = []
        self._progress_hooks = []
        self._postprocessor_hooks = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._num_videos = 0
        self._playlist_level = 0
        self._playlist_urls = set()
        self.cache = Cache(self)
        self.__header_cookies = []

        # compat for API: load plugins if they have not already
        if not all_plugins_loaded.value:
            load_all_plugins()

        stdout = sys.stderr if self.params.get('logtostderr') else sys.stdout
        self._out_files = Namespace(
            out=stdout,
            error=sys.stderr,
            screen=sys.stderr if self.params.get('quiet') else stdout,
        )

        try:
            windows_enable_vt_mode()
        except Exception as e:
            self.write_debug(f'Failed to enable VT mode: {e}')

        # hehe "immutable" namespace
        self._out_files.console = next(filter(supports_terminal_sequences, (sys.stderr, sys.stdout)), None)

        if self.params.get('no_color'):
            if self.params.get('color') is not None:
                self.params.setdefault('_warnings', []).append(
                    'Overwriting params from "color" with "no_color"')
            self.params['color'] = 'no_color'

        term_allow_color = os.getenv('TERM', '').lower() != 'dumb'
        base_no_color = bool(os.getenv('NO_COLOR'))

        def process_color_policy(stream):
            stream_name = {sys.stdout: 'stdout', sys.stderr: 'stderr'}[stream]
            policy = traverse_obj(self.params, ('color', (stream_name, None), {str}, any)) or 'auto'
            if policy in ('auto', 'auto-tty', 'no_color-tty'):
                no_color = base_no_color
                if policy.endswith('tty'):
                    no_color = policy.startswith('no_color')
                if term_allow_color and supports_terminal_sequences(stream):
                    return 'no_color' if no_color else True
                return False
            assert policy in ('always', 'never', 'no_color'), policy
            return {'always': True, 'never': False}.get(policy, policy)

        self._allow_colors = Namespace(**{
            name: process_color_policy(stream)
            for name, stream in self._out_files.items_ if name != 'console'
        })

        system_deprecation = _get_system_deprecation()
        if system_deprecation:
            self.deprecated_feature(system_deprecation.replace('\n', '\n                    '))
        elif self.params.get('warn_when_outdated'):
            if outdated_warning := _get_outdated_warning():
                self.report_warning(outdated_warning)

        if self.params.get('allow_unplayable_formats'):
            self.report_warning(
                f'You have asked for {self._format_err("UNPLAYABLE", self.Styles.EMPHASIS)} formats to be listed/downloaded. '
                'This is a developer option intended for debugging. \n'
                '         If you experience any issues while using this option, '
                f'{self._format_err("DO NOT", self.Styles.ERROR)} open a bug report')

        if self.params.get('bidi_workaround', False):
            try:
                import pty
                master, slave = pty.openpty()
                width = shutil.get_terminal_size().columns
                width_args = [] if width is None else ['-w', str(width)]
                sp_kwargs = {'stdin': subprocess.PIPE, 'stdout': slave, 'stderr': self._out_files.error}
                try:
                    self._output_process = Popen(['bidiv', *width_args], **sp_kwargs)
                except OSError:
                    self._output_process = Popen(['fribidi', '-c', 'UTF-8', *width_args], **sp_kwargs)
                self._output_channel = os.fdopen(master, 'rb')
            except OSError as ose:
                if ose.errno == errno.ENOENT:
                    self.report_warning(
                        'Could not find fribidi executable, ignoring --bidi-workaround. '
                        'Make sure that  fribidi  is an executable file in one of the directories in your $PATH.')
                else:
                    raise

        # Note: this must be after plugins are loaded
        self.params['js_runtimes'] = self.params.get('js_runtimes', {'deno': {}})
        self._clean_js_runtimes(self.params['js_runtimes'])

        self.params['remote_components'] = set(self.params.get('remote_components', ()))
        self._clean_remote_components(self.params['remote_components'])

        self.params['compat_opts'] = set(self.params.get('compat_opts', ()))
        self.params['http_headers'] = HTTPHeaderDict(std_headers, self.params.get('http_headers'))
        self._load_cookies(self.params['http_headers'].get('Cookie'))  # compat
        self.params['http_headers'].pop('Cookie', None)

        if auto_init and auto_init != 'no_verbose_header':
            self.print_debug_header()

        def check_deprecated(param, option, suggestion):
            if self.params.get(param) is not None:
                self.report_warning(f'{option} is deprecated. Use {suggestion} instead')
                return True
            return False

        check_deprecated('useid', '--id', '-o "%(id)s.%(ext)s"')

        for msg in self.params.get('_warnings', []):
            self.report_warning(msg)
        for msg in self.params.get('_deprecation_warnings', []):
            self.deprecated_feature(msg)

        if impersonate_target := self.params.get('impersonate'):
            if not self._impersonate_target_available(impersonate_target):
                raise YoutubeDLError(
                    f'Impersonate target "{impersonate_target}" is not available. '
                    f'Use --list-impersonate-targets to see available targets. '
                    f'You may be missing dependencies required to support this target.')

        if 'list-formats' in self.params['compat_opts']:
            self.params['listformats_table'] = False

        if 'overwrites' not in self.params and self.params.get('nooverwrites') is not None:
            # nooverwrites was unnecessarily changed to overwrites
            # in 0c3d0f51778b153f65c21906031c2e091fcfb641
            # This ensures compatibility with both keys
            self.params['overwrites'] = not self.params['nooverwrites']
        elif self.params.get('overwrites') is None:
            self.params.pop('overwrites', None)
        else:
            self.params['nooverwrites'] = not self.params['overwrites']

        if self.params.get('simulate') is None and any((
            self.params.get('list_thumbnails'),
            self.params.get('listformats'),
            self.params.get('listsubtitles'),
        )):
            self.params['simulate'] = 'list_only'

        self.params.setdefault('forceprint', {})
        self.params.setdefault('print_to_file', {})

        # Compatibility with older syntax
        if not isinstance(params['forceprint'], dict):
            self.params['forceprint'] = {'video': params['forceprint']}

        if auto_init:
            self.add_default_info_extractors()

        if (sys.platform != 'win32'
                and sys.getfilesystemencoding() in ['ascii', 'ANSI_X3.4-1968']
                and not self.params.get('restrictfilenames', False)):
            # Unicode filesystem API will throw errors (#1474, #13027)
            self.report_warning(
                'Assuming --restrict-filenames since file system encoding '
                'cannot encode all characters. '
                'Set the LC_ALL environment variable to fix this.')
            self.params['restrictfilenames'] = True

        self._parse_outtmpl()

        # Creating format selector here allows us to catch syntax errors before the extraction
        self.format_selector = (
            self.params.get('format') if self.params.get('format') in (None, '-')
            else self.params['format'] if callable(self.params['format'])
            else self.build_format_selector(self.params['format']))

        hooks = {
            'post_hooks': self.add_post_hook,
            'progress_hooks': self.add_progress_hook,
            'postprocessor_hooks': self.add_postprocessor_hook,
        }
        for opt, fn in hooks.items():
            for ph in self.params.get(opt, []):
                fn(ph)

        for pp_def_raw in self.params.get('postprocessors', []):
            pp_def = dict(pp_def_raw)
            when = pp_def.pop('when', 'post_process')
            self.add_post_processor(
                get_postprocessor(pp_def.pop('key'))(self, **pp_def),
                when=when)

        def preload_download_archive(fn):
            """Preload the archive, if any is specified"""
            archive = set()
            if fn is None:
                return archive
            elif not is_path_like(fn):
                return fn

            self.write_debug(f'Loading archive file {fn!r}')
            try:
                with locked_file(fn, 'r', encoding='utf-8') as archive_file:
                    for line in archive_file:
                        archive.add(line.strip())
            except OSError as ioe:
                if ioe.errno != errno.ENOENT:
                    raise
            return archive

        self.archive = preload_download_archive(self.params.get('download_archive'))