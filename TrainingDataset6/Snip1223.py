def test_match(script, branch_name, output):
    assert match(Command(script, output))