def test_match(isdir, script, output):
    isdir.return_value = True
    command = Command(script, output)
    assert match(command)