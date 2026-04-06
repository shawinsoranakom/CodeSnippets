def test_not_match(script):
    assert not match(Command(script, "Deleted branch foo (was a1b2c3d)."))