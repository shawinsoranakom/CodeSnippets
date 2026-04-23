def parse_args():
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    def add_parser(*args, **kwargs):
        parser = subcommands.add_parser(*args, **kwargs)
        parser.add_argument(
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
        parser.add_argument(
            "-v", "--verbose", action="count", default=0,
            help="Show verbose output. Use twice to be even more verbose.")
        return parser

    # Subcommands
    build = add_parser(
        "build",
        help="Run configure and make for the selected target"
    )
    configure_build = add_parser(
        "configure-build", help="Run `configure` for the build Python")
    add_parser(
        "make-build", help="Run `make` for the build Python")
    configure_host = add_parser(
        "configure-host", help="Run `configure` for Android")
    make_host = add_parser(
        "make-host", help="Run `make` for Android")

    clean = add_parser(
        "clean",
        help="Delete build directories for the selected target"
    )

    test = add_parser("test", help="Run the testbed app")
    package = add_parser("package", help="Make a release package")
    ci = add_parser("ci", help="Run build, package and test")
    env = add_parser("env", help="Print environment variables")

    # Common arguments
    # --cache-dir option
    for cmd in [configure_host, build, ci]:
        cmd.add_argument(
            "--cache-dir",
            default=os.environ.get("CACHE_DIR"),
            help="The directory to store cached downloads.",
        )

    # --clean option
    for subcommand in [build, configure_build, configure_host, ci]:
        subcommand.add_argument(
            "--clean", action="store_true", default=False, dest="clean",
            help="Delete the relevant build directories first")

    # Allow "all", "build" and "hosts" targets for some commands
    for subcommand in [clean, build]:
        subcommand.add_argument(
            "target",
            nargs="?",
            default="all",
            choices=["all", "build", "hosts"] + HOSTS,
            help=(
                "The host triplet (e.g., aarch64-linux-android), "
                "or 'build' for just the build platform, or 'hosts' for all "
                "host platforms, or 'all' for the build platform and all "
                "hosts. Defaults to 'all'"
            ),
        )

    host_commands = [configure_host, make_host, package, ci]
    if in_source_tree:
        host_commands.append(env)
    for subcommand in host_commands:
        subcommand.add_argument(
            "host", metavar="HOST", choices=HOSTS,
            help="Host triplet: choices=[%(choices)s]")

    for subcommand in [build, configure_build, configure_host, ci]:
        subcommand.add_argument("args", nargs="*",
                                help="Extra arguments to pass to `configure`")

    # Test arguments
    device_group = test.add_mutually_exclusive_group(required=True)
    device_group.add_argument(
        "--connected", metavar="SERIAL", help="Run on a connected device. "
        "Connect it yourself, then get its serial from `adb devices`.")
    device_group.add_argument(
        "--managed", metavar="NAME", help="Run on a Gradle-managed device. "
        "These are defined in `managedDevices` in testbed/app/build.gradle.kts.")

    test.add_argument(
        "--site-packages", metavar="DIR", type=abspath,
        help="Directory to copy as the app's site-packages.")
    test.add_argument(
        "--cwd", metavar="DIR", type=abspath,
        help="Directory to copy as the app's working directory.")
    test.add_argument(
        "args", nargs="*", help=f"Python command-line arguments. "
        f"Separate them from {SCRIPT_NAME}'s own arguments with `--`. "
        f"If neither -c nor -m are included, `-m test` will be prepended, "
        f"which will run Python's own test suite.")

    # Package arguments.
    for subcommand in [package, ci]:
        subcommand.add_argument(
            "-g", action="store_true", default=False, dest="debug",
            help="Include debug information in package")

    # CI arguments
    for subcommand in [test, ci]:
        group = subcommand.add_mutually_exclusive_group(required=subcommand is ci)
        group.add_argument(
            "--fast-ci", action="store_const", dest="ci_mode", const="fast",
            help="Add test arguments for GitHub Actions")
        group.add_argument(
            "--slow-ci", action="store_const", dest="ci_mode", const="slow",
            help="Add test arguments for buildbots")

    return parser.parse_args()