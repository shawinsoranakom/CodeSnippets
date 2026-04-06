def test_match(command, isdir):
    isdir.return_value = True
    assert match(command)