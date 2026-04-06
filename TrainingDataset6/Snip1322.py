def test_match():
    assert match(Command('grep blah .', 'grep: .: Is a directory'))
    assert match(Command(u'grep café .', 'grep: .: Is a directory'))
    assert not match(Command('', ''))