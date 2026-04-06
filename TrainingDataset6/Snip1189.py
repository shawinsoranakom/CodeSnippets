def test_match(cmd, output):
    c = Command(cmd, output)
    assert match(c)