def yum_help(mocker):
    mock = mocker.patch('subprocess.Popen')
    mock.return_value.stdout = BytesIO(bytes(yum_help_text.encode('utf-8')))
    return mock