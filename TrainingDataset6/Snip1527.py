def test_match(script, is_bsd):
    command = Command(script, output(is_bsd))
    assert match(command)