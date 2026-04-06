def test_match(script, output_branch_exists):
    assert match(Command(script, output_branch_exists))