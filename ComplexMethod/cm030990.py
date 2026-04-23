def display_header(use_resources: dict[str, str | None],
                   python_cmd: tuple[str, ...] | None) -> None:
    # Print basic platform information
    print("==", platform.python_implementation(), *sys.version.split())
    print("==", platform.platform(aliased=True),
                  "%s-endian" % sys.byteorder)
    print("== Python build:", ' '.join(get_build_info()))
    print("== cwd:", os.getcwd())

    cpu_count: object = os.cpu_count()
    if cpu_count:
        # The function is new in Python 3.13; mypy doesn't know about it yet:
        process_cpu_count = os.process_cpu_count()  # type: ignore[attr-defined]
        if process_cpu_count and process_cpu_count != cpu_count:
            cpu_count = f"{process_cpu_count} (process) / {cpu_count} (system)"
        print("== CPU count:", cpu_count)
    print("== encodings: locale=%s FS=%s"
          % (locale.getencoding(), sys.getfilesystemencoding()))

    if use_resources:
        text = format_resources(use_resources)
        print(f"== {text}")
    else:
        print("== resources: all test resources are disabled, "
              "use -u option to unskip tests")

    cross_compile = is_cross_compiled()
    if cross_compile:
        print("== cross compiled: Yes")
    if python_cmd:
        cmd = shlex.join(python_cmd)
        print(f"== host python: {cmd}")

        get_cmd = [*python_cmd, '-m', 'platform']
        proc = subprocess.run(
            get_cmd,
            stdout=subprocess.PIPE,
            text=True,
            cwd=os_helper.SAVEDCWD)
        stdout = proc.stdout.replace('\n', ' ').strip()
        if stdout:
            print(f"== host platform: {stdout}")
        elif proc.returncode:
            print(f"== host platform: <command failed with exit code {proc.returncode}>")
    else:
        hostrunner = get_host_runner()
        if hostrunner:
            print(f"== host runner: {hostrunner}")

    # This makes it easier to remember what to set in your local
    # environment when trying to reproduce a sanitizer failure.
    asan = support.check_sanitizer(address=True)
    msan = support.check_sanitizer(memory=True)
    ubsan = support.check_sanitizer(ub=True)
    tsan = support.check_sanitizer(thread=True)
    sanitizers = []
    if asan:
        sanitizers.append("address")
    if msan:
        sanitizers.append("memory")
    if ubsan:
        sanitizers.append("undefined behavior")
    if tsan:
        sanitizers.append("thread")
    if sanitizers:
        print(f"== sanitizers: {', '.join(sanitizers)}")
        for sanitizer, env_var in (
            (asan, "ASAN_OPTIONS"),
            (msan, "MSAN_OPTIONS"),
            (ubsan, "UBSAN_OPTIONS"),
            (tsan, "TSAN_OPTIONS"),
        ):
            options= os.environ.get(env_var)
            if sanitizer and options is not None:
                print(f"== {env_var}={options!r}")

    print(flush=True)