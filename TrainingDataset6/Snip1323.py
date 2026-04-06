def test_get_new_command():
    assert get_new_command(Command('grep blah .', '')) == 'grep -r blah .'
    assert get_new_command(Command(u'grep café .', '')) == u'grep -r café .'