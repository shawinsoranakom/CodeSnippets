def test_match():
    assert match(Command('cs', 'cs: command not found'))
    assert match(Command('cs /etc/', 'cs: command not found'))