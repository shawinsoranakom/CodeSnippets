async def gradle_task(context):
    env = os.environ.copy()
    if context.managed:
        task_prefix = context.managed
    else:
        task_prefix = "connected"
        env["ANDROID_SERIAL"] = context.connected

    # Ensure that CROSS_BUILD_DIR is in the Gradle environment, regardless
    # of whether it was set by environment variable or `--cross-build-dir`.
    env["CROSS_BUILD_DIR"] = CROSS_BUILD_DIR

    if context.ci_mode:
        context.args[0:0] = [
            # See _add_ci_python_opts in libregrtest/main.py.
            "-W", "error", "-bb", "-E",

            # Randomization is disabled because order-dependent failures are
            # much less likely to pass on a rerun in single-process mode.
            "-m", "test",
            f"--{context.ci_mode}-ci", "--single-process", "--no-randomize",
            "--pythoninfo",
        ]

    if not any(arg in context.args for arg in ["-c", "-m"]):
        context.args[0:0] = ["-m", "test"]

    args = [
        gradlew, "--console", "plain", f"{task_prefix}DebugAndroidTest",
    ] + [
        f"-P{name}={value}"
        for name, value in [
            ("python.sitePackages", context.site_packages),
            ("python.cwd", context.cwd),
            (
                "android.testInstrumentationRunnerArguments.pythonArgs",
                json.dumps(context.args),
            ),
        ]
        if value
    ]
    if context.verbose >= 2:
        args.append("--info")
    log_verbose(context, f"> {join_command(args)}\n")

    try:
        async with async_process(
            *args, cwd=TESTBED_DIR, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        ) as process:
            while line := (await process.stdout.readline()).decode(*DECODE_ARGS):
                # Gradle may take several minutes to install SDK packages, so
                # it's worth showing those messages even in non-verbose mode.
                if line.startswith('Preparing "Install'):
                    sys.stdout.write(line)
                else:
                    log_verbose(context, line)

            status = await wait_for(process.wait(), timeout=1)
            if status == 0:
                exit(0)
            else:
                raise CalledProcessError(status, args)
    finally:
        # Gradle does not stop the tests when interrupted.
        if context.connected:
            stop_app(context.connected)