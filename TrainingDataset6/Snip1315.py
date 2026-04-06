def test_match(mocker, command):
    mocker.patch('thefuck.rules.gradle_wrapper.which', return_value=None)

    assert match(command)