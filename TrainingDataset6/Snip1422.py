def test_not_is_arg_url(script):
    assert not is_arg_url(Command(script, ''))