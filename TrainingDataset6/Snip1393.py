def test_not_match(mocker, command):
    mocker.patch('thefuck.rules.nixos_cmd_not_found', return_value=None)
    assert not match(command)