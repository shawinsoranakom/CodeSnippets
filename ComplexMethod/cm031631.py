def main():
    # Look for directories like `iOSTestbed` as an indicator of the platforms
    # that the testbed folder supports. The original source testbed can support
    # many platforms, but when cloned, only one platform is preserved.
    available_platforms = [
        platform
        for platform in ["iOS"]
        if (Path(__file__).parent / f"{platform}Testbed").is_dir()
    ]

    parser = argparse.ArgumentParser(
        description=(
            "Manages the process of testing an Apple Python project "
            "through Xcode."
        ),
    )

    subcommands = parser.add_subparsers(dest="subcommand")
    clone = subcommands.add_parser(
        "clone",
        description=(
            "Clone the testbed project, copying in a Python framework and"
            "any specified application code."
        ),
        help="Clone a testbed project to a new location.",
    )
    clone.add_argument(
        "--framework",
        help=(
            "The location of the XCFramework (or simulator-only slice of an "
            "XCFramework) to use when running the testbed"
        ),
    )
    clone.add_argument(
        "--platform",
        dest="platform",
        choices=available_platforms,
        default=available_platforms[0],
        help=f"The platform to target (default: {available_platforms[0]})",
    )
    clone.add_argument(
        "--app",
        dest="apps",
        action="append",
        default=[],
        help="The location of any code to include in the testbed project",
    )
    clone.add_argument(
        "location",
        help="The path where the testbed will be cloned.",
    )

    run = subcommands.add_parser(
        "run",
        usage=(
            "%(prog)s [-h] [--simulator SIMULATOR] -- "
            "<test arg> [<test arg> ...]"
        ),
        description=(
            "Run a testbed project. The arguments provided after `--` will be "
            "passed to the running iOS process as if they were arguments to "
            "`python -m`."
        ),
        help="Run a testbed project",
    )
    run.add_argument(
        "--platform",
        dest="platform",
        choices=available_platforms,
        default=available_platforms[0],
        help=f"The platform to target (default: {available_platforms[0]})",
    )
    run.add_argument(
        "--simulator",
        help=(
            "The name of the simulator to use (eg: 'iPhone 16e'). Defaults to "
            "the most recently released 'entry level' iPhone device. Device "
            "architecture and OS version can also be specified; e.g., "
            "`--simulator 'iPhone 16 Pro,arch=arm64,OS=26.0'` would run on "
            "an ARM64 iPhone 16 Pro simulator running iOS 26.0."
        ),
    )
    run.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    try:
        pos = sys.argv.index("--")
        testbed_args = sys.argv[1:pos]
        test_args = sys.argv[pos + 1 :]
    except ValueError:
        testbed_args = sys.argv[1:]
        test_args = []

    context = parser.parse_args(testbed_args)

    if context.subcommand == "clone":
        clone_testbed(
            source=Path(__file__).parent.resolve(),
            target=Path(context.location).resolve(),
            framework=Path(context.framework).resolve()
            if context.framework
            else None,
            platform=context.platform,
            apps=[Path(app) for app in context.apps],
        )
    elif context.subcommand == "run":
        if test_args:
            if not (
                Path(__file__).parent
                / "Python.xcframework"
                / TEST_SLICES[context.platform]
                / "bin"
            ).is_dir():
                print(
                    "Testbed does not contain a compiled Python framework. "
                    f"Use `python {sys.argv[0]} clone ...` to create a "
                    "runnable clone of this testbed."
                )
                sys.exit(20)

            run_testbed(
                platform=context.platform,
                simulator=context.simulator,
                verbose=context.verbose,
                args=test_args,
            )
        else:
            print(
                "Must specify test arguments "
                f"(e.g., {sys.argv[0]} run -- test)"
            )
            print()
            parser.print_help(sys.stderr)
            sys.exit(21)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)