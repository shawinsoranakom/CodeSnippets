def script_main(download, download_playlist, **kwargs):
    logging.basicConfig(format='[%(levelname)s] %(message)s')

    def print_version():
        version = get_version(
            kwargs['repo_path'] if 'repo_path' in kwargs else __version__
        )
        log.i(
            'version {}, a tiny downloader that scrapes the web.'.format(
                version
            )
        )

    parser = argparse.ArgumentParser(
        prog='you-get',
        usage='you-get [OPTION]... URL...',
        description='A tiny downloader that scrapes the web',
        add_help=False,
    )
    parser.add_argument(
        '-V', '--version', action='store_true',
        help='Print version and exit'
    )
    parser.add_argument(
        '-h', '--help', action='store_true',
        help='Print this help message and exit'
    )

    dry_run_grp = parser.add_argument_group(
        'Dry-run options', '(no actual downloading)'
    )
    dry_run_grp = dry_run_grp.add_mutually_exclusive_group()
    dry_run_grp.add_argument(
        '-i', '--info', action='store_true', help='Print extracted information'
    )
    dry_run_grp.add_argument(
        '-u', '--url', action='store_true',
        help='Print extracted information with URLs'
    )
    dry_run_grp.add_argument(
        '--json', action='store_true',
        help='Print extracted URLs in JSON format'
    )

    download_grp = parser.add_argument_group('Download options')
    download_grp.add_argument(
        '-n', '--no-merge', action='store_true', default=False,
        help='Do not merge video parts'
    )
    download_grp.add_argument(
        '--no-caption', action='store_true',
        help='Do not download captions (subtitles, lyrics, danmaku, ...)'
    )
    download_grp.add_argument(
        '--post', '--postfix', dest='postfix', action='store_true', default=False,
        help='Postfix downloaded files with unique identifiers'
    )
    download_grp.add_argument(
        '--pre', '--prefix', dest='prefix', metavar='PREFIX', default=None,
        help='Prefix downloaded files with string'
    )
    download_grp.add_argument(
        '-f', '--force', action='store_true', default=False,
        help='Force overwriting existing files'
    )
    download_grp.add_argument(
        '--skip-existing-file-size-check', action='store_true', default=False,
        help='Skip existing file without checking file size'
    )
    download_grp.add_argument(
        '-F', '--format', metavar='STREAM_ID',
        help='Set video format to STREAM_ID'
    )
    download_grp.add_argument(
        '-O', '--output-filename', metavar='FILE', help='Set output filename'
    )
    download_grp.add_argument(
        '-o', '--output-dir', metavar='DIR', default='.',
        help='Set output directory'
    )
    download_grp.add_argument(
        '-p', '--player', metavar='PLAYER',
        help='Stream extracted URL to a PLAYER'
    )
    download_grp.add_argument(
        '-c', '--cookies', metavar='COOKIES_FILE',
        help='Load cookies.txt or cookies.sqlite'
    )
    download_grp.add_argument(
        '-t', '--timeout', metavar='SECONDS', type=int, default=600,
        help='Set socket timeout'
    )
    download_grp.add_argument(
        '-d', '--debug', action='store_true',
        help='Show traceback and other debug info'
    )
    download_grp.add_argument(
        '-I', '--input-file', metavar='FILE', type=argparse.FileType('r'),
        help='Read non-playlist URLs from FILE'
    )
    download_grp.add_argument(
        '-P', '--password', help='Set video visit password to PASSWORD'
    )
    download_grp.add_argument(
        '-l', '--playlist', action='store_true',
        help='Prefer to download a playlist'
    )

    playlist_grp = parser.add_argument_group('Playlist optional options')
    playlist_grp.add_argument(
        '--first', metavar='FIRST',
        help='the first number'
    )
    playlist_grp.add_argument(
        '--last', metavar='LAST',
        help='the last number'
    )
    playlist_grp.add_argument(
        '--size', '--page-size', metavar='PAGE_SIZE',
        help='the page size number'
    )

    download_grp.add_argument(
        '-a', '--auto-rename', action='store_true', default=False,
        help='Auto rename same name different files'
    )

    download_grp.add_argument(
        '-k', '--insecure', action='store_true', default=False,
        help='ignore ssl errors'
    )

    proxy_grp = parser.add_argument_group('Proxy options')
    proxy_grp = proxy_grp.add_mutually_exclusive_group()
    proxy_grp.add_argument(
        '-x', '--http-proxy', metavar='HOST:PORT',
        help='Use an HTTP proxy for downloading'
    )
    proxy_grp.add_argument(
        '-y', '--extractor-proxy', metavar='HOST:PORT',
        help='Use an HTTP proxy for extracting only'
    )
    proxy_grp.add_argument(
        '--no-proxy', action='store_true', help='Never use a proxy'
    )
    proxy_grp.add_argument(
        '-s', '--socks-proxy', metavar='HOST:PORT or USERNAME:PASSWORD@HOST:PORT',
        help='Use an SOCKS5 proxy for downloading'
    )

    download_grp.add_argument('--stream', help=argparse.SUPPRESS)
    download_grp.add_argument('--itag', help=argparse.SUPPRESS)

    download_grp.add_argument('-m', '--m3u8', action='store_true', default=False,
        help = 'download video using an m3u8 url')


    parser.add_argument('URL', nargs='*', help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.help:
        print_version()
        parser.print_help()
        sys.exit()
    if args.version:
        print_version()
        sys.exit()

    if args.debug:
        # Set level of root logger to DEBUG
        logging.getLogger().setLevel(logging.DEBUG)

    global force
    global skip_existing_file_size_check
    global dry_run
    global json_output
    global player
    global extractor_proxy
    global output_filename
    global auto_rename
    global insecure
    global m3u8
    global postfix
    global prefix
    output_filename = args.output_filename
    extractor_proxy = args.extractor_proxy

    info_only = args.info
    if args.force:
        force = True
    if args.skip_existing_file_size_check:
        skip_existing_file_size_check = True
    if args.auto_rename:
        auto_rename = True
    if args.url:
        dry_run = True
    if args.json:
        json_output = True
        # to fix extractors not use VideoExtractor
        dry_run = True
        info_only = False

    if args.cookies:
        load_cookies(args.cookies)

    if args.m3u8:
        m3u8 = True

    caption = True
    stream_id = args.format or args.stream or args.itag
    if args.no_caption:
        caption = False
    if args.player:
        player = args.player
        caption = False

    if args.insecure:
        # ignore ssl
        insecure = True

    postfix = args.postfix
    prefix = args.prefix

    if args.no_proxy:
        set_http_proxy('')
    else:
        set_http_proxy(args.http_proxy)
    if args.socks_proxy:
        set_socks_proxy(args.socks_proxy)

    URLs = []
    if args.input_file:
        logging.debug('you are trying to load urls from %s', args.input_file)
        if args.playlist:
            log.e(
                "reading playlist from a file is unsupported "
                "and won't make your life easier"
            )
            sys.exit(2)
        URLs.extend(args.input_file.read().splitlines())
        args.input_file.close()
    URLs.extend(args.URL)

    if not URLs:
        parser.print_help()
        sys.exit()

    socket.setdefaulttimeout(args.timeout)

    try:
        extra = {'args': args}
        if extractor_proxy:
            extra['extractor_proxy'] = extractor_proxy
        if stream_id:
            extra['stream_id'] = stream_id
        download_main(
            download, download_playlist,
            URLs, args.playlist,
            output_dir=args.output_dir, merge=not args.no_merge,
            info_only=info_only, json_output=json_output, caption=caption,
            password=args.password,
            **extra
        )
    except KeyboardInterrupt:
        if args.debug:
            raise
        else:
            sys.exit(1)
    except UnicodeEncodeError:
        if args.debug:
            raise
        log.e(
            '[error] oops, the current environment does not seem to support '
            'Unicode.'
        )
        log.e('please set it to a UTF-8-aware locale first,')
        log.e(
            'so as to save the video (with some Unicode characters) correctly.'
        )
        log.e('you can do it like this:')
        log.e('    (Windows)    % chcp 65001 ')
        log.e('    (Linux)      $ LC_CTYPE=en_US.UTF-8')
        sys.exit(1)
    except Exception:
        if not args.debug:
            log.e('[error] oops, something went wrong.')
            log.e(
                'don\'t panic, c\'est la vie. please try the following steps:'
            )
            log.e('  (1) Rule out any network problem.')
            log.e('  (2) Make sure you-get is up-to-date.')
            log.e('  (3) Check if the issue is already known, on')
            log.e('        https://github.com/soimort/you-get/wiki/Known-Bugs')
            log.e('        https://github.com/soimort/you-get/issues')
            log.e('  (4) Run the command with \'--debug\' option,')
            log.e('      and report this issue with the full output.')
        else:
            print_version()
            log.i(args)
            raise
        sys.exit(1)