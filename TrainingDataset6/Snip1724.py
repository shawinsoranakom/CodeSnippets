def test_is_app(script, names, result):
    assert is_app(Command(script, ''), *names) == result