def test_match(output):
    assert match(Command('git tag alert', output))
    assert not match(Command('git tag alert', ''))