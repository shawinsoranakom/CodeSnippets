def test_not_match(file_exists, file_access, script, output, exists, callable):
    file_exists.return_value = exists
    file_access.return_value = callable
    assert not match(Command(script, output))