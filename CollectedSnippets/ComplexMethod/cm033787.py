def run():
    parser = argparse.ArgumentParser(prog="validate-modules")
    parser.add_argument('plugins', nargs='+',
                        help='Path to module/plugin or module/plugin directory')
    parser.add_argument('-w', '--warnings', help='Show warnings',
                        action='store_true')
    parser.add_argument('--exclude', help='RegEx exclusion pattern',
                        type=re_compile)
    parser.add_argument('--arg-spec', help='Analyze module argument spec',
                        action='store_true', default=False)
    parser.add_argument('--format', choices=['json', 'plain'], default='plain',
                        help='Output format. Default: "%(default)s"')
    parser.add_argument('--output', default='-',
                        help='Output location, use "-" for stdout. '
                             'Default "%(default)s"')
    parser.add_argument('--collection',
                        help='Specifies the path to the collection, when '
                             'validating files within a collection. Ensure '
                             'that ANSIBLE_COLLECTIONS_PATH is set so the '
                             'contents of the collection can be located')
    parser.add_argument('--collection-version',
                        help='The collection\'s version number used to check '
                             'deprecations')
    parser.add_argument('--plugin-type',
                        default='module',
                        help='The plugin type to validate. Defaults to %(default)s')
    parser.add_argument('--original-plugins')

    args = parser.parse_args()

    args.plugins = [m.rstrip('/') for m in args.plugins]

    reporter = Reporter()
    git_cache = GitCache.create(args.original_plugins, args.plugin_type)

    check_dirs = set()

    routing = None
    if args.collection:
        routing_file = 'meta/runtime.yml'
    else:
        routing_file = 'lib/ansible/config/ansible_builtin_runtime.yml'

    if os.path.isfile(routing_file):
        try:
            with open(routing_file) as f:
                routing = yaml.safe_load(f)
        except yaml.error.MarkedYAMLError as ex:
            print('%s:%d:%d: YAML load failed: %s' % (routing_file, ex.context_mark.line + 1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        except Exception as ex:  # pylint: disable=broad-except
            print('%s:%d:%d: YAML load failed: %s' % (routing_file, 0, 0, re.sub(r'\s+', ' ', str(ex))))

    for plugin in args.plugins:
        if os.path.isfile(plugin):
            path = plugin
            if args.exclude and args.exclude.search(path):
                continue
            if ModuleValidator.is_on_rejectlist(path):
                continue
            with ModuleValidator(path, collection=args.collection, collection_version=args.collection_version,
                                 analyze_arg_spec=args.arg_spec,
                                 git_cache=git_cache, reporter=reporter, routing=routing,
                                 plugin_type=args.plugin_type) as mv1:
                mv1.validate()
                check_dirs.add(os.path.dirname(path))

        for root, dirs, files in os.walk(plugin):
            basedir = root[len(plugin) + 1:].split('/', 1)[0]
            if basedir in REJECTLIST_DIRS:
                continue
            for dirname in dirs:
                if root == plugin and dirname in REJECTLIST_DIRS:
                    continue
                path = os.path.join(root, dirname)
                if args.exclude and args.exclude.search(path):
                    continue
                check_dirs.add(path)

            for filename in files:
                path = os.path.join(root, filename)
                if args.exclude and args.exclude.search(path):
                    continue
                if ModuleValidator.is_on_rejectlist(path):
                    continue
                with ModuleValidator(path, collection=args.collection, collection_version=args.collection_version,
                                     analyze_arg_spec=args.arg_spec,
                                     git_cache=git_cache, reporter=reporter, routing=routing,
                                     plugin_type=args.plugin_type) as mv2:
                    mv2.validate()

    if not args.collection and args.plugin_type == 'module':
        for path in sorted(check_dirs):
            pv = PythonPackageValidator(path, reporter=reporter)
            pv.validate()

    if args.format == 'plain':
        sys.exit(reporter.plain(warnings=args.warnings, output=args.output))
    else:
        sys.exit(reporter.json(warnings=args.warnings, output=args.output))