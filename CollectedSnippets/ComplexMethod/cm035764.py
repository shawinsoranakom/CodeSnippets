def _check_source_code_in_dir(temp_dir):
    # assert there is a folder called 'code' in the temp_dir
    code_dir = os.path.join(temp_dir, 'code')
    assert os.path.exists(code_dir)
    assert os.path.isdir(code_dir)

    # check the source file is the same as the current code base
    assert os.path.exists(os.path.join(code_dir, 'pyproject.toml'))

    # The source code should only include the `openhands` folder,
    # and pyproject.toml & poetry.lock that are needed to build the runtime image
    assert set(os.listdir(code_dir)) == {
        'openhands',
        'pyproject.toml',
        'poetry.lock',
    }
    assert os.path.exists(os.path.join(code_dir, 'openhands'))
    assert os.path.isdir(os.path.join(code_dir, 'openhands'))

    # make sure the version from the pyproject.toml is the same as the current version
    with open(os.path.join(code_dir, 'pyproject.toml'), 'r') as f:
        pyproject = toml.load(f)

    _pyproject_version = pyproject['tool']['poetry']['version']
    assert _pyproject_version == version('openhands-ai')