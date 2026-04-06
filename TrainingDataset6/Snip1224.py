def test_not_match(script, branch_name, output):
    assert not match(Command(script, output))