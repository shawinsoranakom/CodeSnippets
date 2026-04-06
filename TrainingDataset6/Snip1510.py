def test_not_match(which, script, output, which_result):
    which.return_value = which_result
    assert not match(Command(script, output))