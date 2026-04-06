def test_match(script, file):
    assert match(Command(script, output(file)))