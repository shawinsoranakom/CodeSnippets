def test_get_new_command():
    """ Replace the Alt+Space character by a simple space """
    assert (get_new_command(Command(u'ps -ef | grep foo', ''))
            == 'ps -ef | grep foo')