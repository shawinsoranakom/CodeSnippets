def test_match(output, script, branch_name):
    assert match(Command(script, output))