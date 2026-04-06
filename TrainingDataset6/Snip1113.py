def test_get_new_command(set_help, output, script, result):
    set_help(help_text)
    assert result in get_new_command(Command(script, output))