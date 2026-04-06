def test_match(output):
    assert match(Command('dnf', output))