def test_get_new_comman(script, result):
    new_command = get_new_command(
        Command(script, output.format('wlan0')))
    assert new_command == result