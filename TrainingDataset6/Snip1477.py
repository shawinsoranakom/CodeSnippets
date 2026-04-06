def test_get_new_command(mocker, command, result):
    patch = mocker.patch(
        'thefuck.rules.react_native_command_unrecognized.Popen')
    patch.return_value.stdout = BytesIO(stdout)
    assert get_new_command(command)[0] == result