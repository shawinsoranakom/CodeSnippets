def test_match(option):
    assert match(Command("pacman -{}v meat".format(option), bad_output))