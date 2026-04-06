def test_match_management_cmd(script, output):
    assert match(Command(script, output))