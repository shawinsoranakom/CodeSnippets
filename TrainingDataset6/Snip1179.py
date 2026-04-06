def test_get_new_command():
    assert (get_new_command(Command('git branch list', '')) ==
            shell.and_('git branch --delete list', 'git branch'))