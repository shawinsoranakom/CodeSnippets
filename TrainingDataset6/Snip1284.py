def test_match(output, script, target):
    assert match(Command(script, output))