def test_get_new_command(tmux_ambiguous):
    assert get_new_command(Command('tmux list', tmux_ambiguous))\
        == ['tmux list-keys', 'tmux list-panes', 'tmux list-windows']