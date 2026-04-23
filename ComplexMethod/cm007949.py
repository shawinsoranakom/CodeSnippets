def run_tests(*tests, pattern=None, ci=False, flaky: bool | None = None):
    # XXX: hatch uses `tests` if no arguments are passed
    run_core = 'core' in tests or 'tests' in tests or (not pattern and not tests)
    run_download = 'download' in tests
    run_flaky = flaky or (flaky is None and not ci)

    pytest_args = args.pytest_args or os.getenv('HATCH_TEST_ARGS', '')
    arguments = ['pytest', '-Werror', '--tb=short', *shlex.split(pytest_args)]
    if ci:
        arguments.append('--color=yes')
    if pattern:
        arguments.extend(['-k', pattern])
    if run_core:
        arguments.extend(['-m', 'not download'])
    elif run_download:
        arguments.extend(['-m', 'download'])
    else:
        arguments.extend(
            test if '/' in test
            else f'test/test_download.py::TestDownload::test_{fix_test_name(test)}'
            for test in tests)
    if not run_flaky:
        arguments.append('--disallow-flaky')

    print(f'Running {arguments}', flush=True)
    try:
        return subprocess.call(arguments)
    except FileNotFoundError:
        pass

    arguments = [sys.executable, '-Werror', '-m', 'unittest']
    if pattern:
        arguments.extend(['-k', pattern])
    if run_core:
        print('"pytest" needs to be installed to run core tests', file=sys.stderr, flush=True)
        return 1
    elif run_download:
        arguments.append('test.test_download')
    else:
        arguments.extend(
            f'test.test_download.TestDownload.test_{test}' for test in tests)

    print(f'Running {arguments}', flush=True)
    return subprocess.call(arguments)