def test_match(script, output):
    command = Command(script, output.format(error))
    assert match(command)