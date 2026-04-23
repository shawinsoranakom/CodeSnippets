def raw_command(
    cmd: c.Iterable[str],
    capture: bool,
    env: t.Optional[dict[str, str]] = None,
    data: t.Optional[str] = None,
    cwd: t.Optional[str] = None,
    explain: bool = False,
    stdin: t.Optional[t.Union[t.IO[bytes], int]] = None,
    stdout: t.Optional[t.Union[t.IO[bytes], int]] = None,
    interactive: bool = False,
    output_stream: t.Optional[OutputStream] = None,
    cmd_verbosity: int = 1,
    str_errors: str = 'strict',
    error_callback: t.Optional[c.Callable[[SubprocessError], None]] = None,
) -> tuple[t.Optional[str], t.Optional[str]]:
    """Run the specified command and return stdout and stderr as a tuple."""
    output_stream = output_stream or OutputStream.AUTO

    if capture and interactive:
        raise InternalError('Cannot combine capture=True with interactive=True.')

    if data and interactive:
        raise InternalError('Cannot combine data with interactive=True.')

    if stdin and interactive:
        raise InternalError('Cannot combine stdin with interactive=True.')

    if stdout and interactive:
        raise InternalError('Cannot combine stdout with interactive=True.')

    if stdin and data:
        raise InternalError('Cannot combine stdin with data.')

    if stdout and not capture:
        raise InternalError('Redirection of stdout requires capture=True to avoid redirection of stderr to stdout.')

    if output_stream != OutputStream.AUTO and capture:
        raise InternalError(f'Cannot combine {output_stream=} with capture=True.')

    if output_stream != OutputStream.AUTO and interactive:
        raise InternalError(f'Cannot combine {output_stream=} with interactive=True.')

    if not cwd:
        cwd = os.getcwd()

    if not env:
        env = common_environment()

    cmd = list(cmd)

    escaped_cmd = shlex.join(cmd)

    if capture:
        description = 'Run'
    elif interactive:
        description = 'Interactive'
    else:
        description = 'Stream'

    description += ' command'

    with_types = []

    if data:
        with_types.append('data')

    if stdin:
        with_types.append('stdin')

    if stdout:
        with_types.append('stdout')

    if with_types:
        description += f' with {"/".join(with_types)}'

    display.info(f'{description}: {escaped_cmd}', verbosity=cmd_verbosity, truncate=True)
    display.info('Working directory: %s' % cwd, verbosity=2)

    program = find_executable(cmd[0], cwd=cwd, path=env['PATH'], required=False)

    if program:
        display.info('Program found: %s' % program, verbosity=2)

    for key in sorted(env.keys()):
        display.info('%s=%s' % (key, env[key]), verbosity=2)

    if explain:
        return None, None

    communicate = False

    if stdin is not None:
        data = None
    elif data is not None:
        stdin = subprocess.PIPE
        communicate = True
    elif interactive:
        pass  # allow the subprocess access to our stdin
    else:
        stdin = subprocess.DEVNULL

    if not interactive:
        # When not running interactively, send subprocess stdout/stderr through a pipe.
        # This isolates the stdout/stderr of the subprocess from the current process, and also hides the current TTY from it, if any.
        # This prevents subprocesses from sharing stdout/stderr with the current process or each other.
        # Doing so allows subprocesses to safely make changes to their file handles, such as making them non-blocking (ssh does this).
        # This also maintains consistency between local testing and CI systems, which typically do not provide a TTY.
        # To maintain output ordering, a single pipe is used for both stdout/stderr when not capturing output unless the output stream is ORIGINAL.
        stdout = stdout or subprocess.PIPE
        stderr = subprocess.PIPE if capture or output_stream == OutputStream.ORIGINAL else subprocess.STDOUT
        communicate = True
    else:
        stderr = None

    start = time.time()
    process = None

    try:
        try:
            process = subprocess.Popen(cmd, env=env, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)  # pylint: disable=consider-using-with
        except FileNotFoundError as ex:
            raise ApplicationError('Required program "%s" not found.' % cmd[0]) from ex

        if communicate:
            data_bytes = to_optional_bytes(data)

            stdout_bytes, stderr_bytes = communicate_with_process(
                name=cmd[0],
                process=process,
                stdin=data_bytes,
                stdout=stdout == subprocess.PIPE,
                stderr=stderr == subprocess.PIPE,
                capture=capture,
                output_stream=output_stream,
            )

            stdout_text = to_optional_text(stdout_bytes, str_errors) or ''
            stderr_text = to_optional_text(stderr_bytes, str_errors) or ''
        else:
            process.wait()
            stdout_text, stderr_text = None, None
    finally:
        if process and process.returncode is None:
            process.kill()
            display.info('')  # the process we're interrupting may have completed a partial line of output
            display.notice('Killed command to avoid an orphaned child process during handling of an unexpected exception.')

    status = process.returncode
    runtime = time.time() - start

    display.info('Command exited with status %s after %s seconds.' % (status, runtime), verbosity=4)

    if status == 0:
        return stdout_text, stderr_text

    raise SubprocessError(cmd, status, stdout_text, stderr_text, runtime, error_callback)