def test_match(brew_unknown_cmd):
    assert match(Command('brew inst', brew_unknown_cmd))
    for command in _brew_commands():
        assert not match(Command('brew ' + command, ''))