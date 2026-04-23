def create_worker_process(runtests: WorkerRunTests, output_fd: int,
                          tmp_dir: StrPath | None = None) -> subprocess.Popen[str]:
    worker_json = runtests.as_json()

    cmd = runtests.create_python_cmd()
    cmd.extend(['-m', 'test.libregrtest.worker', worker_json])

    env = dict(os.environ)
    if tmp_dir is not None:
        env['TMPDIR'] = tmp_dir
        env['TEMP'] = tmp_dir
        env['TMP'] = tmp_dir

    # The subcommand is run with a temporary output which means it is not a TTY
    # and won't auto-color. The test results are printed to stdout so if we can
    # color that have the subprocess use color.
    if can_colorize(file=sys.stdout):
        env['FORCE_COLOR'] = '1'

    # Running the child from the same working directory as regrtest's original
    # invocation ensures that TEMPDIR for the child is the same when
    # sysconfig.is_python_build() is true. See issue 15300.
    #
    # Emscripten and WASI Python must start in the Python source code directory
    # to get 'python.js' or 'python.wasm' file. Then worker_process() changes
    # to a temporary directory created to run tests.
    work_dir = os_helper.SAVEDCWD

    kwargs: dict[str, Any] = dict(
        env=env,
        stdout=output_fd,
        # bpo-45410: Write stderr into stdout to keep messages order
        stderr=output_fd,
        text=True,
        close_fds=True,
        cwd=work_dir,
    )

    # Don't use setsid() in tests using TTY
    test_name = runtests.tests[0]
    if USE_PROCESS_GROUP and test_name not in NEED_TTY:
        kwargs['start_new_session'] = True

    # Include the test name in the TSAN log file name
    if 'TSAN_OPTIONS' in env:
        parts = env['TSAN_OPTIONS'].split(' ')
        for i, part in enumerate(parts):
            if part.startswith('log_path='):
                parts[i] = f'{part}.{test_name}'
                break
        env['TSAN_OPTIONS'] = ' '.join(parts)

    # Pass json_file to the worker process
    json_file = runtests.json_file
    json_file.configure_subprocess(kwargs)

    with json_file.inherit_subprocess():
        return subprocess.Popen(cmd, **kwargs)