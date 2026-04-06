def test_not_match(file_exists, script, output, exists):
    file_exists.return_value = exists
    assert not match(Command(script, output))