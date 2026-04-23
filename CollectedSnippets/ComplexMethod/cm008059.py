def parseOpts(overrideArguments=None, ignore_config_files='if_override'):  # noqa: N803
    PACKAGE_NAME = 'yt-dlp'

    root = Config(create_parser())
    if ignore_config_files == 'if_override':
        ignore_config_files = overrideArguments is not None

    def read_config(*paths):
        path = os.path.join(*paths)
        conf = Config.read_file(path, default=None)
        if conf is not None:
            return conf, path

    def _load_from_config_dirs(config_dirs):
        for config_dir in config_dirs:
            head, tail = os.path.split(config_dir)
            assert tail == PACKAGE_NAME or config_dir == os.path.join(compat_expanduser('~'), f'.{PACKAGE_NAME}')

            yield read_config(head, f'{PACKAGE_NAME}.conf')
            if tail.startswith('.'):  # ~/.PACKAGE_NAME
                yield read_config(head, f'{PACKAGE_NAME}.conf.txt')
            yield read_config(config_dir, 'config')
            yield read_config(config_dir, 'config.txt')

    def add_config(label, path=None, func=None):
        """ Adds config and returns whether to continue """
        if root.parse_known_args()[0].ignoreconfig:
            return False
        elif func:
            assert path is None
            args, current_path = next(
                filter(None, _load_from_config_dirs(func(PACKAGE_NAME))), (None, None))
        else:
            current_path = os.path.join(path, 'yt-dlp.conf')
            args = Config.read_file(current_path, default=None)
        if args is not None:
            root.append_config(args, current_path, label=label)
        return True

    def load_configs():
        yield not ignore_config_files
        yield add_config('Portable', get_executable_path())
        yield add_config('Home', expand_path(root.parse_known_args()[0].paths.get('home', '')).strip())
        yield add_config('User', func=get_user_config_dirs)
        yield add_config('System', func=get_system_config_dirs)

    opts = optparse.Values({'verbose': True, 'print_help': False})
    try:
        try:
            if overrideArguments is not None:
                root.append_config(overrideArguments, label='Override')
            else:
                root.append_config(sys.argv[1:], label='Command-line')
            loaded_all_configs = all(load_configs())
        except ValueError as err:
            raise root.parser.error(err)

        if loaded_all_configs:
            # If ignoreconfig is found inside the system configuration file,
            # the user configuration is removed
            if root.parse_known_args()[0].ignoreconfig:
                user_conf = next((i for i, conf in enumerate(root.configs) if conf.label == 'User'), None)
                if user_conf is not None:
                    root.configs.pop(user_conf)

        try:
            root.configs[0].load_configs()  # Resolve any aliases using --config-location
        except ValueError as err:
            raise root.parser.error(err)

        opts, args = root.parse_args()
    except optparse.OptParseError:
        with contextlib.suppress(optparse.OptParseError):
            opts, _ = root.parse_known_args(strict=False)
        raise
    except (SystemExit, KeyboardInterrupt):
        opts.verbose = False
        raise
    finally:
        verbose = opts.verbose and f'\n{root}'.replace('\n| ', '\n[debug] ')[1:]
        if verbose:
            write_string(f'{verbose}\n')
        if opts.print_help:
            if verbose:
                write_string('\n')
            root.parser.print_help()
    if opts.print_help:
        sys.exit()
    return root.parser, opts, args