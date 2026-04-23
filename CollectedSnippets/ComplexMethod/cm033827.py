def main() -> None:
    """Main program entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()
    paths = [path for path in paths if path not in vendored_paths]  # FUTURE: define the exclusions in config so the paths can be skipped earlier

    if not paths:
        return

    python_version = os.environ['ANSIBLE_TEST_TARGET_PYTHON_VERSION']
    controller_python_versions = os.environ['ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS'].split(',')
    remote_only_python_versions = os.environ['ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS'].split(',')

    contexts = (
        MyPyContext('ansible-test', ['test/lib/ansible_test/'], controller_python_versions),
        MyPyContext('ansible-test', ['test/lib/ansible_test/_util/target/'], remote_only_python_versions),
        MyPyContext('ansible-core', ['lib/ansible/'], controller_python_versions),
        MyPyContext('ansible-core', ['lib/ansible/modules/', 'lib/ansible/module_utils/'], remote_only_python_versions),
        MyPyContext('ansible-core', ['test/units/'], controller_python_versions),
        MyPyContext('ansible-core', ['test/units/modules/', 'test/units/module_utils/'], remote_only_python_versions),
        MyPyContext('packaging', ['packaging/'], controller_python_versions),
    )

    unfiltered_messages: list[SanityMessage] = []

    for context in contexts:
        if python_version not in context.python_versions:
            continue

        unfiltered_messages.extend(test_context(python_version, context, paths))

    notices = []
    messages = []

    for message in unfiltered_messages:
        if message.level != 'error':
            notices.append(message)
            continue

        match = re.search(r'^(?P<message>.*) {2}\[(?P<code>.*)]$', message.message)

        messages.append(
            SanityMessage(
                message=match.group('message'),
                path=message.path,
                line=message.line,
                column=message.column,
                level=message.level,
                code=match.group('code'),
            )
        )

    # FUTURE: provide a way for script based tests to report non-error messages (in this case, notices)

    # The following error codes from mypy indicate that results are incomplete.
    # That prevents the test from completing successfully, just as if mypy were to traceback or generate unexpected output.
    fatal_error_codes = {
        'import',
        'syntax',
    }

    fatal_errors = [message for message in messages if message.code in fatal_error_codes]

    if fatal_errors:
        error_message = '\n'.join(error.format() for error in fatal_errors)
        raise Exception(f'Encountered {len(fatal_errors)} fatal errors reported by mypy:\n{error_message}')

    paths_set = set(paths)

    # Only report messages for paths that were specified as targets.
    # Imports in our code are followed by mypy in order to perform its analysis, which is important for accurate results.
    # However, it will also report issues on those files, which is not the desired behavior.
    messages = [message for message in messages if message.path in paths_set]

    for message in messages:
        print(message.format())