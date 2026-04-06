def test_match():
    assert match(Command('rm -rf /', 'add --no-preserve-root'))