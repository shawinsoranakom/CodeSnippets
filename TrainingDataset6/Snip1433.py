def test_get_new_command(option):
    new_command = get_new_command(Command("pacman -{}v meat".format(option), ""))
    assert new_command == "pacman -{}v meat".format(option.upper())