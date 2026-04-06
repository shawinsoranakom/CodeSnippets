def test_match(script, result):
    output = get_output('source')
    assert match(Command(script, output))
    assert get_new_command(Command(script, output)) == result