def test_not_match(cmd, output):
    c = Command(cmd, output)
    assert not match(c)