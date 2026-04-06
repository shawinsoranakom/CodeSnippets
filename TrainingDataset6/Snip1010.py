def test_match(output):
    assert match(Command('sudo apt update', output))