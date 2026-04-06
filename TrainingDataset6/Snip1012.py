def test_get_new_command(output):
    new_command = get_new_command(Command('sudo apt update', output))
    assert new_command == 'sudo apt list --upgradable'

    new_command = get_new_command(Command('apt update', output))
    assert new_command == 'apt list --upgradable'