def test_match(pip_unknown_cmd, pip_unknown_cmd_without_recommend):
    assert match(Command('pip instatl', pip_unknown_cmd))
    assert not match(Command('pip i',
                             pip_unknown_cmd_without_recommend))