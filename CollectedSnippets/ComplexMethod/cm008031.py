def print_debug_header(self):
        if not self.params.get('verbose'):
            return

        def get_encoding(stream):
            ret = str(getattr(stream, 'encoding', f'missing ({type(stream).__name__})'))
            additional_info = []
            if os.environ.get('TERM', '').lower() == 'dumb':
                additional_info.append('dumb')
            if not supports_terminal_sequences(stream):
                additional_info.append('No VT' if WINDOWS_VT_MODE.value is False else 'No ANSI')
            if additional_info:
                ret = f'{ret} ({",".join(additional_info)})'
            return ret

        encoding_str = 'Encodings: locale {}, fs {}, pref {}, {}'.format(
            locale.getpreferredencoding(),
            sys.getfilesystemencoding(),
            self.get_encoding(),
            ', '.join(
                f'{key} {get_encoding(stream)}' for key, stream in self._out_files.items_
                if stream is not None and key != 'console'),
        )

        logger = self.params.get('logger')
        if logger:
            write_debug = lambda msg: logger.debug(f'[debug] {msg}')
            write_debug(encoding_str)
        else:
            write_string(f'[debug] {encoding_str}\n', encoding=None)
            write_debug = lambda msg: self._write_string(f'[debug] {msg}\n')

        source = detect_variant()
        if VARIANT not in (None, 'pip'):
            source += '*'
        klass = type(self)
        write_debug(join_nonempty(
            f'{REPOSITORY.rpartition("/")[2]} version',
            _make_label(ORIGIN, CHANNEL.partition('@')[2] or __version__, __version__),
            f'[{RELEASE_GIT_HEAD[:9]}]' if RELEASE_GIT_HEAD else '',
            '' if source == 'unknown' else f'({source})',
            '' if IN_CLI.value else 'API' if klass == YoutubeDL else f'API:{self.__module__}.{klass.__qualname__}',
            delim=' '))

        if not IN_CLI.value:
            write_debug(f'params: {self.params}')

        import_extractors()
        lazy_extractors = LAZY_EXTRACTORS.value
        if lazy_extractors is None:
            write_debug('Lazy loading extractors is disabled')
        elif not lazy_extractors:
            write_debug('Lazy loading extractors is forcibly disabled')
        if self.params['compat_opts']:
            write_debug('Compatibility options: {}'.format(', '.join(self.params['compat_opts'])))

        if current_git_head():
            write_debug(f'Git HEAD: {current_git_head()}')
        write_debug(system_identifier())

        exe_versions, ffmpeg_features = FFmpegPostProcessor.get_versions_and_features(self)
        ffmpeg_features = {key for key, val in ffmpeg_features.items() if val}
        if ffmpeg_features:
            exe_versions['ffmpeg'] += ' ({})'.format(','.join(sorted(ffmpeg_features)))

        exe_versions['rtmpdump'] = rtmpdump_version()
        exe_versions['phantomjs'] = PhantomJSwrapper._version()
        exe_str = ', '.join(
            f'{exe} {v}' for exe, v in sorted(exe_versions.items()) if v
        ) or 'none'
        write_debug(f'exe versions: {exe_str}')

        from .compat.compat_utils import get_package_info
        from .dependencies import available_dependencies

        write_debug('Optional libraries: %s' % (', '.join(sorted({
            join_nonempty(*get_package_info(m)) for m in available_dependencies.values()
        })) or 'none'))

        if not self.params.get('js_runtimes'):
            write_debug('JS runtimes: none (disabled)')
        else:
            write_debug('JS runtimes: %s' % (', '.join(sorted(
                f'{name} (unknown)' if runtime is None
                else join_nonempty(
                    runtime.info.name,
                    runtime.info.version + (' (unsupported)' if runtime.info.supported is False else ''),
                )
                for name, runtime in self._js_runtimes.items() if runtime is None or runtime.info is not None
            )) or 'none'))

        write_debug(f'Proxy map: {self.proxies}')
        write_debug(f'Request Handlers: {", ".join(rh.RH_NAME for rh in self._request_director.handlers.values())}')

        for plugin_type, plugins in (('Extractor', plugin_ies), ('Post-Processor', plugin_pps)):
            display_list = [
                klass.__name__ if klass.__name__ == name else f'{klass.__name__} as {name}'
                for name, klass in plugins.value.items()]
            if plugin_type == 'Extractor':
                display_list.extend(f'{plugins[-1].IE_NAME.partition("+")[2]} ({parent.__name__})'
                                    for parent, plugins in plugin_ies_overrides.value.items())
            if not display_list:
                continue
            write_debug(f'{plugin_type} Plugins: {", ".join(sorted(display_list))}')

        plugin_dirs_msg = 'none'
        if not plugin_dirs.value:
            plugin_dirs_msg = 'none (disabled)'
        else:
            found_plugin_directories = plugin_directories()
            if found_plugin_directories:
                plugin_dirs_msg = ', '.join(found_plugin_directories)

        write_debug(f'Plugin directories: {plugin_dirs_msg}')