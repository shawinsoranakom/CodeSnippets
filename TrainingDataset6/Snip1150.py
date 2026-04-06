def test_not_match(path_exists, output, script, target, exists):
    path_exists.return_value = exists
    assert not match(Command(script, output))