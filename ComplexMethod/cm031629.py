def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "A tool for managing the build, package and test process of "
            "CPython on Apple platforms."
        ),
    )
    parser.suggest_on_error = True
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    clean = subcommands.add_parser(
        "clean",
        help="Delete all build directories",
    )

    configure_build = subcommands.add_parser(
        "configure-build", help="Run `configure` for the build Python"
    )
    make_build = subcommands.add_parser(
        "make-build", help="Run `make` for the build Python"
    )
    configure_host = subcommands.add_parser(
        "configure-host",
        help="Run `configure` for a specific platform and target",
    )
    make_host = subcommands.add_parser(
        "make-host",
        help="Run `make` for a specific platform and target",
    )
    package = subcommands.add_parser(
        "package",
        help="Create a release package for the platform",
    )
    build = subcommands.add_parser(
        "build",
        help="Build all platform targets and create the XCframework",
    )
    test = subcommands.add_parser(
        "test",
        help="Run the testbed for a specific platform",
    )
    ci = subcommands.add_parser(
        "ci",
        help="Run build, package, and test",
    )

    # platform argument
    for cmd in [clean, configure_host, make_host, package, build, test, ci]:
        cmd.add_argument(
            "platform",
            choices=HOSTS.keys(),
            help="The target platform to build",
        )

    # host triple argument
    for cmd in [configure_host, make_host]:
        cmd.add_argument(
            "host",
            help="The host triple to build (e.g., arm64-apple-ios-simulator)",
        )
    # optional host triple argument
    for cmd in [clean, build, test]:
        cmd.add_argument(
            "host",
            nargs="?",
            default="all",
            help=(
                "The host triple to build (e.g., arm64-apple-ios-simulator), "
                "or 'build' for just the build platform, or 'hosts' for all "
                "host platforms, or 'all' for the build platform and all "
                "hosts. Defaults to 'all'"
            ),
        )

    # --cross-build-dir argument
    for cmd in [
        clean,
        configure_build,
        make_build,
        configure_host,
        make_host,
        build,
        package,
        test,
        ci,
    ]:
        cmd.add_argument(
            "--cross-build-dir",
            action="store",
            default=os.environ.get("CROSS_BUILD_DIR"),
            dest="cross_build_dir",
            type=Path,
            help=(
                "Path to the cross-build directory "
                f"(default: {CROSS_BUILD_DIR}). Can also be set "
                "with the CROSS_BUILD_DIR environment variable."
            ),
        )

    # --clean option
    for cmd in [configure_build, configure_host, build, package, test, ci]:
        cmd.add_argument(
            "--clean",
            action="store_true",
            default=False,
            dest="clean",
            help="Delete the relevant build directories first",
        )

    # --cache-dir option
    for cmd in [configure_host, build, ci]:
        cmd.add_argument(
            "--cache-dir",
            default=os.environ.get("CACHE_DIR"),
            help="The directory to store cached downloads.",
        )

    # --simulator option
    for cmd in [test, ci]:
        cmd.add_argument(
            "--simulator",
            help=(
                "The name of the simulator to use (eg: 'iPhone 16e'). "
                "Defaults to the most recently released 'entry level' "
                "iPhone device. Device architecture and OS version can also "
                "be specified; e.g., "
                "`--simulator 'iPhone 16 Pro,arch=arm64,OS=26.0'` would "
                "run on an ARM64 iPhone 16 Pro simulator running iOS 26.0."
            ),
        )
        group = cmd.add_mutually_exclusive_group()
        group.add_argument(
            "--fast-ci",
            action="store_const",
            dest="ci_mode",
            const="fast",
            help="Add test arguments for GitHub Actions",
        )
        group.add_argument(
            "--slow-ci",
            action="store_const",
            dest="ci_mode",
            const="slow",
            help="Add test arguments for buildbots",
        )

    for subcommand in [configure_build, configure_host, build, ci]:
        subcommand.add_argument(
            "args", nargs="*", help="Extra arguments to pass to `configure`"
        )

    return parser.parse_args()