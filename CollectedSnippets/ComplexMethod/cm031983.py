def main():
    args = parser.parse_args()
    if not args.openssl and not args.libressl and not args.awslc:
        args.openssl = list(OPENSSL_RECENT_VERSIONS)
        args.libressl = list(LIBRESSL_RECENT_VERSIONS)
        args.awslc = list(AWSLC_RECENT_VERSIONS)
        if not args.disable_ancient:
            args.openssl.extend(OPENSSL_OLD_VERSIONS)
            args.libressl.extend(LIBRESSL_OLD_VERSIONS)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="*** %(levelname)s %(message)s"
    )

    start = datetime.now()

    if args.steps in {'modules', 'tests'}:
        for name in ['Makefile.pre.in', 'Modules/_ssl.c']:
            if not os.path.isfile(os.path.join(PYTHONROOT, name)):
                parser.error(
                    "Must be executed from CPython build dir"
                )
        if not os.path.samefile('python', sys.executable):
            parser.error(
                "Must be executed with ./python from CPython build dir"
            )
        # check for configure and run make
        configure_make()

    # download and register builder
    builds = []
    for build_class, versions in [
        (BuildOpenSSL, args.openssl),
        (BuildLibreSSL, args.libressl),
        (BuildAWSLC, args.awslc),
    ]:
        for version in versions:
            build = build_class(version, args)
            build.install()
            builds.append(build)

    if args.steps in {'modules', 'tests'}:
        for build in builds:
            try:
                build.recompile_pymods()
                build.check_pyssl()
                if args.steps == 'tests':
                    build.run_python_tests(
                        tests=args.tests,
                        network=args.network,
                    )
            except Exception as e:
                log.exception("%s failed", build)
                print("{} failed: {}".format(build, e), file=sys.stderr)
                sys.exit(2)

    log.info("\n{} finished in {}".format(
            args.steps.capitalize(),
            datetime.now() - start
        ))
    print('Python: ', sys.version)
    if args.steps == 'tests':
        if args.tests:
            print('Executed Tests:', ' '.join(args.tests))
        else:
            print('Executed all SSL tests.')

    print('OpenSSL / LibreSSL / AWS-LC versions:')
    for build in builds:
        print("    * {0.library} {0.version}".format(build))