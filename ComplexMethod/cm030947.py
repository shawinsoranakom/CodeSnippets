def run_python_until_end(*args, **env_vars):
    """Used to implement assert_python_*.

    *args are the command line flags to pass to the python interpreter.
    **env_vars keyword arguments are environment variables to set on the process.

    If __run_using_command= is supplied, it must be a list of
    command line arguments to prepend to the command line used.
    Useful when you want to run another command that should launch the
    python interpreter via its own arguments. ["/bin/echo", "--"] for
    example could print the unquoted python command line instead of
    run it.
    """
    env_required = interpreter_requires_environment()
    run_using_command = env_vars.pop('__run_using_command', None)
    cwd = env_vars.pop('__cwd', None)
    if '__isolated' in env_vars:
        isolated = env_vars.pop('__isolated')
    else:
        isolated = not env_vars and not env_required
    cmd_line = [sys.executable, '-X', 'faulthandler']
    if run_using_command:
        cmd_line = run_using_command + cmd_line
    if isolated:
        # isolated mode: ignore Python environment variables, ignore user
        # site-packages, and don't add the current directory to sys.path
        cmd_line.append('-I')
    elif not env_vars and not env_required:
        # ignore Python environment variables
        cmd_line.append('-E')

    # But a special flag that can be set to override -- in this case, the
    # caller is responsible to pass the full environment.
    if env_vars.pop('__cleanenv', None):
        env = {}
        if sys.platform == 'win32':
            # Windows requires at least the SYSTEMROOT environment variable to
            # start Python.
            env['SYSTEMROOT'] = os.environ['SYSTEMROOT']

        # Other interesting environment variables, not copied currently:
        # COMSPEC, HOME, PATH, TEMP, TMPDIR, TMP.
    else:
        # Need to preserve the original environment, for in-place testing of
        # shared library builds.
        env = os.environ.copy()

    # set TERM='' unless the TERM environment variable is passed explicitly
    # see issues #11390 and #18300
    if 'TERM' not in env_vars:
        env['TERM'] = ''

    env.update(env_vars)
    cmd_line.extend(args)
    proc = subprocess.Popen(cmd_line, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env, cwd=cwd)
    with proc:
        try:
            out, err = proc.communicate()
        finally:
            proc.kill()
            subprocess._cleanup()
    rc = proc.returncode
    return _PythonRunResult(rc, out, err), cmd_line