def test_match(tmux_ambiguous):
    assert match(Command('tmux list', tmux_ambiguous))