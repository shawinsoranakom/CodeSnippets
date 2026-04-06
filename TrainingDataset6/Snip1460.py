def test_not_match(isdir, script, output, isdir_result):
    isdir.return_value = isdir_result
    command = Command(script, output)
    assert not match(command)