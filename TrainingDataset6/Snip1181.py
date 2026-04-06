def git_branch(mocker, branches):
    mock = mocker.patch('subprocess.Popen')
    mock.return_value.stdout = BytesIO(branches)
    return mock