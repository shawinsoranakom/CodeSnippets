def test_context(
    python_version: str,
    context: MyPyContext,
    paths: list[str],
) -> list[SanityMessage]:
    """Run mypy tests for the specified context."""
    context_paths = [path for path in paths if any(path.startswith(match_path) for match_path in context.paths)]

    if not context_paths:
        return []

    config_path = config_dir / f'{context.name}.ini'

    # FUTURE: provide a way for script based tests to report progress and other diagnostic information
    # display.info(f'Checking context "{context.name}"', verbosity=1)

    env = os.environ.copy()
    env['MYPYPATH'] = env['PYTHONPATH']

    # The --no-site-packages option should not be used, as it will prevent loading of type stubs from the sanity test virtual environment.

    # Enabling the --warn-unused-configs option would help keep the config files clean.
    # However, the option can only be used when all files in tested contexts are evaluated.
    # Unfortunately sanity tests have no way of making that determination currently.
    # The option is also incompatible with incremental mode and caching.

    cmd = [
        # Below are arguments common to all contexts.
        # They are kept here to avoid repetition in each config file.
        sys.executable,
        '-m', 'mypy',
        '--show-column-numbers',
        '--show-error-codes',
        '--no-error-summary',
        # This is a fairly common pattern in our code, so we'll allow it.
        '--allow-redefinition',
        # Since we specify the path(s) to test, it's important that mypy is configured to use the default behavior of following imports.
        '--follow-imports', 'normal',
        # Incremental results and caching do not provide significant performance benefits.
        # It also prevents the use of the --warn-unused-configs option.
        '--no-incremental',
        '--cache-dir', '/dev/null',
        # The platform is specified here so that results are consistent regardless of what platform the tests are run from.
        # In the future, if testing of other platforms is desired, the platform should become part of the test specification, just like the Python version.
        '--platform', 'linux',
        # Despite what the documentation [1] states, the --python-version option does not cause mypy to search for a corresponding Python executable.
        # It will instead use the Python executable that is used to run mypy itself.
        # The --python-executable option can be used to specify the Python executable, with the default being the executable used to run mypy.
        # As a precaution, that option is used in case the behavior of mypy is updated in the future to match the documentation.
        # That should help guarantee that the Python executable providing type hints is the one used to run mypy.
        # [1] https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-python-version
        '--python-executable', sys.executable,
        '--python-version', python_version,
        # Below are context specific arguments.
        # They are primarily useful for listing individual 'ignore_missing_imports' entries instead of using a global ignore.
        '--config-file', config_path,
    ]  # fmt: skip

    cmd.extend(context_paths)

    try:
        completed_process = subprocess.run(cmd, env=env, capture_output=True, check=True, text=True)
        stdout, stderr = completed_process.stdout, completed_process.stderr

        if stdout or stderr:
            raise Exception(f'{stdout=} {stderr=}')
    except subprocess.CalledProcessError as ex:
        if ex.returncode != 1 or ex.stderr or not ex.stdout:
            raise Exception(f'{ex.stdout=} {ex.stderr=} {ex.returncode=}') from ex

        stdout = ex.stdout

    pattern = re.compile(r'^(?P<path>[^:]*):(?P<line>[0-9]+):((?P<column>[0-9]+):)? (?P<level>[^:]+): (?P<message>.*)$')

    parsed = parse_to_list_of_dict(pattern, stdout or '')

    messages = [
        SanityMessage(
            level=r['level'],
            message=r['message'],
            path=r['path'],
            line=int(r['line']),
            column=int(r.get('column') or '0'),
            code='',  # extracted from error level messages later
        )
        for r in parsed
    ]

    return messages