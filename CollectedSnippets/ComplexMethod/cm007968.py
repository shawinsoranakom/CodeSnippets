def _test(github_repository, note, repo_vars, repo_secrets, inputs, expected, ignore_revision=False):
    inp = inputs.copy()
    inp.setdefault('linux_armv7l', True)
    inp.setdefault('prerelease', False)
    processed = process_inputs(inp)
    source_repo = processed['source_repo'].upper()
    target_repo = processed['target_repo'].upper()
    variables = {k.upper(): v for k, v in repo_vars.items()}
    secrets = {k.upper(): v for k, v in repo_secrets.items()}

    env = {
        # Keep this in sync with prepare.setup_variables in release.yml
        'INPUTS': json.dumps(inp),
        'PROCESSED': json.dumps(processed),
        'REPOSITORY': github_repository,
        'PYPI_PROJECT': variables.get('PYPI_PROJECT') or '',
        'SOURCE_PYPI_PROJECT': variables.get(f'{source_repo}_PYPI_PROJECT') or '',
        'SOURCE_PYPI_SUFFIX': variables.get(f'{source_repo}_PYPI_SUFFIX') or '',
        'TARGET_PYPI_PROJECT': variables.get(f'{target_repo}_PYPI_PROJECT') or '',
        'TARGET_PYPI_SUFFIX': variables.get(f'{target_repo}_PYPI_SUFFIX') or '',
        'SOURCE_ARCHIVE_REPO': variables.get(f'{source_repo}_ARCHIVE_REPO') or '',
        'TARGET_ARCHIVE_REPO': variables.get(f'{target_repo}_ARCHIVE_REPO') or '',
        'HAS_ARCHIVE_REPO_TOKEN': json.dumps(bool(secrets.get('ARCHIVE_REPO_TOKEN'))),
        'HAS_RELEASE_KEY': json.dumps(bool(secrets.get('RELEASE_KEY'))),
    }

    result = setup_variables(env)

    if expected is GENERATE_TEST_DATA:
        print('        {\n' + '\n'.join(f'            {k!r}: {v!r},' for k, v in result.items()) + '\n        }')
        return

    if expected is None:
        assert result is None, f'expected error/None but got dict: {github_repository} {note}'
        return

    exp = expected.copy()
    if ignore_revision:
        assert len(result['version']) == len(exp['version']), f'revision missing: {github_repository} {note}'
        version_is_tag = result['version'] == result['target_tag']
        for dct in (result, exp):
            dct['version'] = '.'.join(dct['version'].split('.')[:3])
            if version_is_tag:
                dct['target_tag'] = dct['version']
    assert result == exp, f'unexpected result: {github_repository} {note}'