def test_not_match():
    assert not match(Command('', ''))
    assert not match(Command('git branch', ''))
    assert not match(Command('git clone foo', ''))
    assert not match(Command('git clone foo bar baz', output_clean))