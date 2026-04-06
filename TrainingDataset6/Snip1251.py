def test_not_match(output, script, branch_name):
    assert not match(Command(script, output))