def test_not_match_good_output(option):
    assert not match(Command("pacman -{}s meat".format(option), good_output))