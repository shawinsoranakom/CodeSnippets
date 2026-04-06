def test_get_new_command(script, is_bsd):
    command = Command(script, output(is_bsd))
    fixed_command = get_new_command(command)
    assert fixed_command == 'mkdir -p /a/b && touch /a/b/c'