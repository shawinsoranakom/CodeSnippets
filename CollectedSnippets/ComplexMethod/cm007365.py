def print_debug_header(self):
        if not self.params.get('verbose'):
            return

        if type('') is not compat_str:
            # Python 2.6 on SLES11 SP1 (https://github.com/ytdl-org/youtube-dl/issues/3326)
            self.report_warning(
                'Your Python is broken! Update to a newer and supported version')

        stdout_encoding = getattr(
            sys.stdout, 'encoding', 'missing (%s)' % type(sys.stdout).__name__)
        encoding_str = (
            '[debug] Encodings: locale %s, fs %s, out %s, pref %s\n' % (
                locale.getpreferredencoding(),
                sys.getfilesystemencoding(),
                stdout_encoding,
                self.get_encoding()))
        write_string(encoding_str, encoding=None)

        writeln_debug = lambda *s: self.write_debug(''.join(s))
        writeln_debug('youtube-dl version ', __version__)
        if _LAZY_LOADER:
            writeln_debug('Lazy loading extractors enabled')
        if ytdl_is_updateable():
            writeln_debug('Single file build')
        try:
            sp = subprocess.Popen(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__)))
            out, err = process_communicate_or_kill(sp)
            out = out.decode().strip()
            if re.match('[0-9a-f]+', out):
                writeln_debug('Git HEAD: ', out)
        except Exception:
            try:
                sys.exc_clear()
            except Exception:
                pass

        def python_implementation():
            impl_name = platform.python_implementation()
            if impl_name == 'PyPy' and hasattr(sys, 'pypy_version_info'):
                return impl_name + ' version %d.%d.%d' % sys.pypy_version_info[:3]
            return impl_name

        def libc_ver():
            try:
                return platform.libc_ver()
            except OSError:  # We may not have access to the executable
                return []

        libc = join_nonempty(*libc_ver(), delim=' ')
        writeln_debug('Python %s (%s %s %s) - %s - %s%s' % (
            platform.python_version(),
            python_implementation(),
            platform.machine(),
            platform.architecture()[0],
            platform_name(),
            OPENSSL_VERSION,
            (' - %s' % (libc, )) if libc else ''
        ))

        exe_versions = FFmpegPostProcessor.get_versions(self)
        exe_versions['rtmpdump'] = rtmpdump_version()
        exe_versions['phantomjs'] = PhantomJSwrapper._version()
        exe_str = ', '.join(
            '%s %s' % (exe, v)
            for exe, v in sorted(exe_versions.items())
            if v
        )
        if not exe_str:
            exe_str = 'none'
        writeln_debug('exe versions: %s' % (exe_str, ))

        proxy_map = {}
        for handler in self._opener.handlers:
            if hasattr(handler, 'proxies'):
                proxy_map.update(handler.proxies)
        writeln_debug('Proxy map: ', compat_str(proxy_map))

        if self.params.get('call_home', False):
            ipaddr = self.urlopen('https://yt-dl.org/ip').read().decode('utf-8')
            writeln_debug('Public IP address: %s' % (ipaddr, ))
            latest_version = self.urlopen(
                'https://yt-dl.org/latest/version').read().decode('utf-8')
            if version_tuple(latest_version) > version_tuple(__version__):
                self.report_warning(
                    'You are using an outdated version (newest version: %s)! '
                    'See https://yt-dl.org/update if you need help updating.' %
                    latest_version)