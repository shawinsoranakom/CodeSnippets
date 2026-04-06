def test_not_march(script, stdout):
    assert not match(Command(script, stdout))