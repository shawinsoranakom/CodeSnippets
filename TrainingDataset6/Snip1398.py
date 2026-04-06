def test_not_match(mocker, script, output, which):
    mocker.patch('thefuck.rules.no_command.which', return_value=which)

    assert not match(Command(script, output))