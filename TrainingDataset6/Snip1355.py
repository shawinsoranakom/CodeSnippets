def test_match(is_not_task):
    assert match(Command('lein rpl', is_not_task))
    assert not match(Command('ls', is_not_task))