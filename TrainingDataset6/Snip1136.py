def test_match():
    """The character before 'grep' is Alt+Space, which happens frequently
    on the Mac when typing the pipe character (Alt+7), and holding the Alt
    key pressed for longer than necessary.

    """
    assert match(Command(u'ps -ef | grep foo',
                         u'-bash:  grep: command not found'))
    assert not match(Command('ps -ef | grep foo', ''))
    assert not match(Command('', ''))