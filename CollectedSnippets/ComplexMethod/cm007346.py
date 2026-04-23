def __init__(self, params=None, auto_init=True):
        """Create a FileDownloader object with the given options."""
        if params is None:
            params = {}
        self._ies = []
        self._ies_instances = {}
        self._pps = []
        self._progress_hooks = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]
        self._err_file = sys.stderr
        self.params = {
            # Default parameters
            'nocheckcertificate': False,
        }
        self.params.update(params)
        self.cache = Cache(self)

        self._header_cookies = []
        self._load_cookies_from_headers(self.params.get('http_headers'))

        def check_deprecated(param, option, suggestion):
            if self.params.get(param) is not None:
                self.report_warning(
                    '%s is deprecated. Use %s instead.' % (option, suggestion))
                return True
            return False

        if check_deprecated('cn_verification_proxy', '--cn-verification-proxy', '--geo-verification-proxy'):
            if self.params.get('geo_verification_proxy') is None:
                self.params['geo_verification_proxy'] = self.params['cn_verification_proxy']

        check_deprecated('autonumber_size', '--autonumber-size', 'output template with %(autonumber)0Nd, where N in the number of digits')
        check_deprecated('autonumber', '--auto-number', '-o "%(autonumber)s-%(title)s.%(ext)s"')
        check_deprecated('usetitle', '--title', '-o "%(title)s-%(id)s.%(ext)s"')

        if params.get('bidi_workaround', False):
            try:
                import pty
                master, slave = pty.openpty()
                width = compat_get_terminal_size().columns
                if width is None:
                    width_args = []
                else:
                    width_args = ['-w', str(width)]
                sp_kwargs = dict(
                    stdin=subprocess.PIPE,
                    stdout=slave,
                    stderr=self._err_file)
                try:
                    self._output_process = subprocess.Popen(
                        ['bidiv'] + width_args, **sp_kwargs
                    )
                except OSError:
                    self._output_process = subprocess.Popen(
                        ['fribidi', '-c', 'UTF-8'] + width_args, **sp_kwargs)
                self._output_channel = os.fdopen(master, 'rb')
            except OSError as ose:
                if ose.errno == errno.ENOENT:
                    self.report_warning('Could not find fribidi executable, ignoring --bidi-workaround . Make sure that  fribidi  is an executable file in one of the directories in your $PATH.')
                else:
                    raise

        if (sys.platform != 'win32'
                and sys.getfilesystemencoding() in ['ascii', 'ANSI_X3.4-1968']
                and not params.get('restrictfilenames', False)):
            # Unicode filesystem API will throw errors (#1474, #13027)
            self.report_warning(
                'Assuming --restrict-filenames since file system encoding '
                'cannot encode all characters. '
                'Set the LC_ALL environment variable to fix this.')
            self.params['restrictfilenames'] = True

        if isinstance(params.get('outtmpl'), bytes):
            self.report_warning(
                'Parameter outtmpl is bytes, but should be a unicode string. '
                'Put  from __future__ import unicode_literals  at the top of your code file or consider switching to Python 3.x.')

        self._setup_opener()

        if auto_init:
            self.print_debug_header()
            self.add_default_info_extractors()

        for pp_def_raw in self.params.get('postprocessors', []):
            pp_class = get_postprocessor(pp_def_raw['key'])
            pp_def = dict(pp_def_raw)
            del pp_def['key']
            pp = pp_class(self, **compat_kwargs(pp_def))
            self.add_post_processor(pp)

        for ph in self.params.get('progress_hooks', []):
            self.add_progress_hook(ph)

        register_socks_protocols()