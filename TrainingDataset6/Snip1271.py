def test_match(output):
    assert match(Command('git rebase --continue', output))
    assert not match(Command('git rebase --continue', ''))
    assert not match(Command('git rebase --skip', ''))