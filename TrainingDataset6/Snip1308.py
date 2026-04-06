def test_not_match():
    assert not match(Command('go run', 'go run: no go files listed'))