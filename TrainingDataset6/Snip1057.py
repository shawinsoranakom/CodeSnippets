def test_not_match(command, isdir):
    isdir.return_value = False
    assert not match(command)