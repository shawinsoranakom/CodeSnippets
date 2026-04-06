def test_match_management_subcmd(script, output):
    assert match(Command(script, output))