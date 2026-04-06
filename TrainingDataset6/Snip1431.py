def test_not_match_bad_output(option):
    assert not match(Command("pacman -{}v meat".format(option), bad_output))