def test_match(output, script):
    assert match(Command(script, output))