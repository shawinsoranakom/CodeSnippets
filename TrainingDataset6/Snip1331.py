def test_get_new_command(mocker):
    mock = mocker.patch('subprocess.Popen')
    mock.return_value.stdout = BytesIO(b'serve \nbuild \ndefault \n')
    command = Command('gulp srve', output('srve'))
    assert get_new_command(command) == ['gulp serve', 'gulp default']