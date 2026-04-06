def test_match(script, command):
    assert match(Command(script, output.format(command)))