def test_get_new_command(brew_unknown_cmd, brew_unknown_cmd2):
    assert (get_new_command(Command('brew inst', brew_unknown_cmd))
            == ['brew list', 'brew install', 'brew uninstall'])

    cmds = get_new_command(Command('brew instaa', brew_unknown_cmd2))
    assert 'brew install' in cmds
    assert 'brew uninstall' in cmds