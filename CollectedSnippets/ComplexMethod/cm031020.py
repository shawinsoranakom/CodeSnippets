def _parse_args(args, **kwargs):
    # Defaults
    ns = Namespace()
    for k, v in kwargs.items():
        if not hasattr(ns, k):
            raise TypeError('%r is an invalid keyword argument '
                            'for this function' % k)
        setattr(ns, k, v)

    parser = _create_parser()
    # Issue #14191: argparse doesn't support "intermixed" positional and
    # optional arguments. Use parse_known_args() as workaround.
    ns.args = parser.parse_known_args(args=args, namespace=ns)[1]
    for arg in ns.args:
        if arg.startswith('-'):
            parser.error("unrecognized arguments: %s" % arg)

    if ns.timeout is not None:
        # Support "--timeout=" (no value) so Makefile.pre.pre TESTTIMEOUT
        # can be used by "make buildbottest" and "make test".
        if ns.timeout != "":
            try:
                ns.timeout = float(ns.timeout)
            except ValueError:
                parser.error(f"invalid timeout value: {ns.timeout!r}")
        else:
            ns.timeout = None

    # Continuous Integration (CI): common options for fast/slow CI modes
    if ns.slow_ci or ns.fast_ci:
        # Similar to options:
        #   -j0 --randomize --fail-env-changed --rerun --slowest --verbose3
        if ns.use_mp is None:
            ns.use_mp = 0
        ns.randomize = True
        ns.fail_env_changed = True
        if ns.python is None:
            ns.rerun = True
        ns.print_slow = True
        if not ns.verbose:
            ns.verbose3 = True
        else:
            # --verbose has the priority over --verbose3
            pass
    else:
        ns._add_python_opts = False

    # --singleprocess overrides -jN option
    if ns.single_process:
        ns.use_mp = None

    # When both --slow-ci and --fast-ci options are present,
    # --slow-ci has the priority
    if ns.slow_ci:
        # Similar to: -u "all" --timeout=1200
        if ns.use is None:
            ns.use = []
        ns.use[:0] = [('all', None)]
        if ns.timeout is None:
            ns.timeout = 1200  # 20 minutes
    elif ns.fast_ci:
        # Similar to: -u "all,-cpu" --timeout=600
        if ns.use is None:
            ns.use = []
        ns.use[:0] = [('all', None), ('-cpu', None)]
        if ns.timeout is None:
            ns.timeout = 600  # 10 minutes

    if ns.single and ns.fromfile:
        parser.error("-s and -f don't go together!")
    if ns.trace:
        if ns.use_mp is not None:
            if not Py_DEBUG:
                parser.error("need --with-pydebug to use -T and -j together")
        else:
            print(
                "Warning: collecting coverage without -j is imprecise. Configure"
                " --with-pydebug and run -m test -T -j for best results.",
                file=sys.stderr
            )
    if ns.python is not None:
        if ns.use_mp is None:
            parser.error("-p requires -j!")
        # The "executable" may be two or more parts, e.g. "node python.js"
        ns.python = shlex.split(ns.python)
    if ns.failfast and not (ns.verbose or ns.verbose3):
        parser.error("-G/--failfast needs either -v or -W")
    if ns.pgo and (ns.verbose or ns.rerun or ns.verbose3):
        parser.error("--pgo/-v don't go together!")
    if ns.pgo_extended:
        ns.pgo = True  # pgo_extended implies pgo

    if ns.nowindows:
        print("Warning: the --nowindows (-n) option is deprecated. "
              "Use -vv to display assertions in stderr.", file=sys.stderr)

    if ns.quiet:
        ns.verbose = 0
    if ns.timeout is not None:
        if ns.timeout <= 0:
            ns.timeout = None
    if ns.use:
        for r, v in ns.use:
            if r == 'all':
                for r in ALL_RESOURCES:
                    ns.use_resources[r] = None
            elif r == 'none':
                ns.use_resources.clear()
            elif r[0] == '-':
                r = r[1:]
                ns.use_resources.pop(r, None)
            else:
                ns.use_resources[r] = v
    if ns.random_seed is not None:
        ns.randomize = True
    if ns.no_randomize:
        ns.randomize = False
    if ns.verbose:
        ns.header = True

    # When -jN option is used, a worker process does not use --verbose3
    # and so -R 3:3 -jN --verbose3 just works as expected: there is no false
    # alarm about memory leak.
    if ns.huntrleaks and ns.verbose3 and ns.use_mp is None:
        # run_single_test() replaces sys.stdout with io.StringIO if verbose3
        # is true. In this case, huntrleaks sees an write into StringIO as
        # a memory leak, whereas it is not (gh-71290).
        ns.verbose3 = False
        print("WARNING: Disable --verbose3 because it's incompatible with "
              "--huntrleaks without -jN option",
              file=sys.stderr)

    if ns.forever:
        # --forever implies --failfast
        ns.failfast = True

    if ns.huntrleaks:
        warmup, repetitions, _ = ns.huntrleaks
        if warmup < 1 or repetitions < 1:
            msg = ("Invalid values for the --huntrleaks/-R parameters. The "
                   "number of warmups and repetitions must be at least 1 "
                   "each (1:1).")
            print(msg, file=sys.stderr, flush=True)
            sys.exit(2)

    ns.prioritize = [
        test
        for test_list in (ns.prioritize or ())
        for test in test_list
    ]

    return ns