def test(context: argparse.Namespace, host: str | None = None) -> None:  # noqa: PT028
    """The implementation of the "test" command."""
    if host is None:
        host = context.host

    if context.clean:
        clean(context, "test")

    with group(f"Test {'XCframework' if host in {'all', 'hosts'} else host}"):
        timestamp = str(time.time_ns())[:-6]
        testbed_dir = (
            CROSS_BUILD_DIR / f"{context.platform}-testbed.{timestamp}"
        )
        if host in {"all", "hosts"}:
            framework_path = (
                CROSS_BUILD_DIR / context.platform / "Python.xcframework"
            )
        else:
            build_arch = platform.machine()
            host_arch = host.split("-")[0]

            if not host.endswith("-simulator"):
                print("Skipping test suite non-simulator build.")
                return
            elif build_arch != host_arch:
                print(
                    f"Skipping test suite for an {host_arch} build "
                    f"on an {build_arch} machine."
                )
                return
            else:
                framework_path = (
                    CROSS_BUILD_DIR
                    / host
                    / f"Platforms/Apple/{context.platform}"
                    / f"Frameworks/{apple_multiarch(host)}"
                )

        run([
            sys.executable,
            "Platforms/Apple/testbed",
            "clone",
            "--platform",
            context.platform,
            "--framework",
            framework_path,
            testbed_dir,
        ])

        run(
            [
                sys.executable,
                testbed_dir,
                "run",
                "--verbose",
            ]
            + (
                ["--simulator", str(context.simulator)]
                if context.simulator
                else []
            )
            + [
                "--",
                "test",
                f"--{context.ci_mode or 'fast'}-ci",
                "--single-process",
                "--no-randomize",
                "--pythoninfo",
                # Timeout handling requires subprocesses; explicitly setting
                # the timeout to -1 disables the faulthandler.
                "--timeout=-1",
                # Adding Python options requires the use of a subprocess to
                # start a new Python interpreter.
                "--dont-add-python-opts",
            ]
        )