def test_not_match():
    assert not match(Command('az provider', no_suggestions))