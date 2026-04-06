def test_match(output):
    assert match(Command('git add dist/*.js', output))
    assert not match(Command('git add dist/*.js', ''))