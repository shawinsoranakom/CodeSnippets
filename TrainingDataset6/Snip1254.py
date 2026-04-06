def test_match():
    assert match(Command('git push', error_msg('foo', 'bar')))