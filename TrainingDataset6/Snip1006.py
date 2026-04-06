def set_help(mocker):
    mock = mocker.patch('subprocess.Popen')

    def _set_text(text):
        mock.return_value.stdout = BytesIO(text)

    return _set_text