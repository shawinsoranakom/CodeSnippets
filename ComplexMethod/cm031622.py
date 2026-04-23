def main():
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="subcommand")

    install_emscripten_cmd = subcommands.add_parser(
        "install-emscripten",
        help="Install the appropriate version of Emscripten",
    )

    build = subcommands.add_parser("build", help="Build everything")
    build.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", "host", "build"],
        help=(
            "What should be built. 'build' for just the build platform, or "
            "'host' for the host platform, or 'all' for both. Defaults to 'all'."
        ),
    )

    configure_build = subcommands.add_parser(
        "configure-build-python", help="Run `configure` for the build Python"
    )

    make_mpdec_cmd = subcommands.add_parser(
        "make-mpdec",
        help="Clone mpdec repo, configure and build it for emscripten",
    )

    make_libffi_cmd = subcommands.add_parser(
        "make-libffi",
        help="Clone libffi repo, configure and build it for emscripten",
    )

    make_dependencies_cmd = subcommands.add_parser(
        "make-dependencies",
        help="Build all static library dependencies",
    )

    for cmd in [make_mpdec_cmd, make_libffi_cmd, make_dependencies_cmd]:
        cmd.add_argument(
            "--check-up-to-date",
            action="store_true",
            default=False,
            help=("If passed, will fail if dependency is out of date"),
        )

    make_build = subcommands.add_parser(
        "make-build-python", help="Run `make` for the build Python"
    )

    configure_host = subcommands.add_parser(
        "configure-host",
        help=(
            "Run `configure` for the host/emscripten "
            "(pydebug builds are inferred from the build Python)"
        ),
    )

    make_host = subcommands.add_parser(
        "make-host", help="Run `make` for the host/emscripten"
    )

    run = subcommands.add_parser(
        "run",
        help="Run the built emscripten Python",
    )
    run.add_argument(
        "--test",
        action="store_true",
        default=False,
        help=(
            "Add the default test arguments to the beginning of the command. "
            "Default arguments loaded from Platforms/emscripten/config.toml"
        ),
    )
    run.add_argument(
        "--pythoninfo",
        action="store_true",
        default=False,
        help="Run -m test.pythoninfo",
    )
    run.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help=(
            "Arguments to pass to the emscripten Python "
            "(use '--' to separate from run options)",
        ),
    )
    add_cross_build_dir_option(run)

    clean = subcommands.add_parser(
        "clean", help="Delete files and directories created by this script"
    )
    clean.add_argument(
        "target",
        nargs="?",
        default="host",
        choices=["all", "host", "build"],
        help=(
            "What should be cleaned. 'build' for just the build platform, or "
            "'host' for the host platform, or 'all' for both. Defaults to 'host'."
        ),
    )

    for subcommand in (
        install_emscripten_cmd,
        build,
        configure_build,
        make_libffi_cmd,
        make_mpdec_cmd,
        make_dependencies_cmd,
        make_build,
        configure_host,
        make_host,
        clean,
    ):
        subcommand.add_argument(
            "--quiet",
            action="store_true",
            default="QUIET" in os.environ,
            dest="quiet",
            help=(
                "Redirect output from subprocesses to a log file. "
                "Can also be set with the QUIET environment variable."
            ),
        )
        add_cross_build_dir_option(subcommand)
        subcommand.add_argument(
            "--emsdk-cache",
            action="store",
            default=os.environ.get("EMSDK_CACHE"),
            dest="emsdk_cache",
            help=(
                "Path to emsdk cache directory. If provided, validates that "
                "the required emscripten version is installed. "
                "Can also be set with the EMSDK_CACHE environment variable."
            ),
        )

    for subcommand in configure_build, configure_host:
        subcommand.add_argument(
            "--clean",
            action="store_true",
            default=False,
            dest="clean",
            help="Delete any relevant directories before building",
        )

    for subcommand in build, configure_build, configure_host:
        subcommand.add_argument(
            "args", nargs="*", help="Extra arguments to pass to `configure`"
        )

    for subcommand in build, configure_host:
        subcommand.add_argument(
            "--host-runner",
            action="store",
            default=None,
            dest="host_runner",
            help="Command template for running the emscripten host "
            "(default: use nvm to install the node version specified in config.toml)",
        )

    context = parser.parse_args()
    context.emsdk_cache = getattr(context, "emsdk_cache", None)
    context.cross_build_dir = getattr(context, "cross_build_dir", None)
    context.check_up_to_date = getattr(context, "check_up_to_date", False)

    if context.emsdk_cache:
        context.emsdk_cache = Path(context.emsdk_cache).absolute()

    context.build_paths = get_build_paths(
        context.cross_build_dir, context.emsdk_cache
    )

    dispatch = {
        "install-emscripten": install_emscripten,
        "make-libffi": make_emscripten_libffi,
        "make-mpdec": make_mpdec,
        "make-dependencies": make_dependencies,
        "configure-build-python": configure_build_python,
        "make-build-python": make_build_python,
        "configure-host": configure_emscripten_python,
        "make-host": make_emscripten_python,
        "build": build_target,
        "run": run_emscripten_python,
        "clean": clean_contents,
    }

    if not context.subcommand:
        # No command provided, display help and exit
        print(
            "Expected one of",
            ", ".join(sorted(dispatch.keys())),
            file=sys.stderr,
        )
        parser.print_help(sys.stderr)
        sys.exit(1)
    dispatch[context.subcommand](context)