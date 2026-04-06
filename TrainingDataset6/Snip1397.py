def test_match(mocker, script, output):
    mocker.patch('thefuck.rules.no_command.which', return_value=None)

    assert match(Command(script, output))