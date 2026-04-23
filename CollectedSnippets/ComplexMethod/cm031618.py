async def logcat_task(context, initial_devices):
    # Gradle may need to do some large downloads of libraries and emulator
    # images. This will happen during find_device in --managed mode, or find_pid
    # in --connected mode.
    startup_timeout = 600
    serial = await wait_for(find_device(context, initial_devices), startup_timeout)
    pid = await wait_for(find_pid(serial), startup_timeout)

    # `--pid` requires API level 24 or higher.
    #
    # `--binary` mode is used in order to detect which messages end with a
    # newline, which most of the other modes don't indicate (except `--format
    # long`). For example, every time pytest runs a test, it prints a "." and
    # flushes the stream. Each "." becomes a separate log message, but we should
    # show them all on the same line.
    args = [adb, "-s", serial, "logcat", "--pid", pid,  "--binary"]
    logcat_started = False
    async with async_process(
        *args, stdout=subprocess.PIPE, stderr=None
    ) as process:
        while True:
            try:
                priority, tag, message = await read_logcat(process.stdout)
                logcat_started = True
            except asyncio.IncompleteReadError:
                break

            # Exclude high-volume messages which are rarely useful.
            if context.verbose < 2 and "from python test_syslog" in message:
                continue

            # Put high-level messages on stderr so they're highlighted in the
            # buildbot logs. This will include Python's own stderr.
            stream = sys.stderr if priority >= LogPriority.WARN else sys.stdout

            # The app's stdout and stderr should be passed through transparently
            # to our own corresponding streams.
            if tag in ["python.stdout", "python.stderr"]:
                global python_started
                python_started = True
                stream.write(message)
                stream.flush()
            else:
                # Non-Python messages add a lot of noise, but they may
                # sometimes help explain a failure. Format them in the same way
                # as `logcat --format tag`.
                formatted = f"{priority.name[0]}/{tag}: {message}"
                if not formatted.endswith("\n"):
                    formatted += "\n"
                log_verbose(context, formatted, stream)

        # If the device disconnects while logcat is running, which always
        # happens in --managed mode, some versions of adb return non-zero.
        # Distinguish this from a logcat startup error by checking whether we've
        # received any logcat messages yet.
        status = await wait_for(process.wait(), timeout=1)
        if status != 0 and not logcat_started:
            raise CalledProcessError(status, args)