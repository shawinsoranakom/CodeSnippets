def test_not_match(mocker, exists, command, gradlew, which):
    mocker.patch('thefuck.rules.gradle_wrapper.which', return_value=which)
    exists.return_value = gradlew

    assert not match(command)