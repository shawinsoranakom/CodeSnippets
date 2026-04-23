def _real_main(argv=None):
    setproctitle('yt-dlp')

    parser, opts, all_urls, ydl_opts = parse_options(argv)

    if print_extractor_information(opts, all_urls):
        return

    # We may need ffmpeg_location without having access to the YoutubeDL instance
    # See https://github.com/yt-dlp/yt-dlp/issues/2191
    if opts.ffmpeg_location:
        FFmpegPostProcessor._ffmpeg_location.set(opts.ffmpeg_location)

    # load all plugins into the global lookup
    plugin_dirs.value = opts.plugin_dirs
    if plugin_dirs.value:
        _load_all_plugins()

    with YoutubeDL(ydl_opts) as ydl:
        pre_process = opts.update_self or opts.rm_cachedir
        actual_use = all_urls or opts.load_info_filename

        if opts.rm_cachedir:
            ydl.cache.remove()

        try:
            updater = Updater(ydl, opts.update_self)
            if opts.update_self and updater.update() and actual_use and updater.cmd:
                return updater.restart()
        except Exception:
            traceback.print_exc()
            ydl._download_retcode = 100

        if opts.list_impersonate_targets:

            known_targets = [
                # List of simplified targets we know are supported,
                # to help users know what dependencies may be required.
                (ImpersonateTarget('chrome'), 'curl_cffi'),
                (ImpersonateTarget('safari'), 'curl_cffi'),
                (ImpersonateTarget('firefox'), 'curl_cffi>=0.10'),
                (ImpersonateTarget('edge'), 'curl_cffi'),
                (ImpersonateTarget('tor'), 'curl_cffi>=0.11'),
            ]

            available_targets = ydl._get_available_impersonate_targets()

            def make_row(target, handler):
                return [
                    join_nonempty(target.client.title(), target.version, delim='-') or '-',
                    join_nonempty((target.os or '').title(), target.os_version, delim='-') or '-',
                    handler,
                ]

            rows = [make_row(target, handler) for target, handler in available_targets]

            for known_target, known_handler in known_targets:
                if not any(
                    known_target in target and known_handler.startswith(handler)
                    for target, handler in available_targets
                ):
                    rows.insert(0, [
                        ydl._format_out(text, ydl.Styles.SUPPRESS)
                        for text in make_row(known_target, f'{known_handler} (unavailable)')
                    ])

            ydl.to_screen('[info] Available impersonate targets')
            ydl.to_stdout(render_table(['Client', 'OS', 'Source'], rows, extra_gap=2, delim='-'))
            return

        if not actual_use:
            if pre_process:
                return ydl._download_retcode

            args = sys.argv[1:] if argv is None else argv
            ydl.warn_if_short_id(args)

            # Show a useful error message and wait for keypress if not launched from shell on Windows
            if not args and os.name == 'nt' and getattr(sys, 'frozen', False):
                import ctypes.wintypes
                import msvcrt

                kernel32 = ctypes.WinDLL('Kernel32')

                buffer = (1 * ctypes.wintypes.DWORD)()
                attached_processes = kernel32.GetConsoleProcessList(buffer, 1)
                # If we only have a single process attached, then the executable was double clicked
                # When using `pyinstaller` with `--onefile`, two processes get attached
                is_onefile = hasattr(sys, '_MEIPASS') and os.path.basename(sys._MEIPASS).startswith('_MEI')
                if attached_processes == 1 or (is_onefile and attached_processes == 2):
                    print(parser._generate_error_message(
                        'Do not double-click the executable, instead call it from a command line.\n'
                        'Please read the README for further information on how to use yt-dlp: '
                        'https://github.com/yt-dlp/yt-dlp#readme'))
                    msvcrt.getch()
                    _exit(2)
            parser.error(
                'You must provide at least one URL.\n'
                'Type yt-dlp --help to see a list of all options.')

        parser.destroy()
        try:
            if opts.load_info_filename is not None:
                if all_urls:
                    ydl.report_warning('URLs are ignored due to --load-info-json')
                return ydl.download_with_info_file(expand_path(opts.load_info_filename))
            else:
                return ydl.download(all_urls)
        except DownloadCancelled:
            ydl.to_screen('Aborting remaining downloads')
            return 101