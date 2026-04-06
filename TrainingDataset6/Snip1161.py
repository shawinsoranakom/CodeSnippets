def test_not_match(script, output_branch_exists):
    assert not match(Command(script, ""))