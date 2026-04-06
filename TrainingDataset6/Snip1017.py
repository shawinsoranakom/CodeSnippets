def test_not_match():
    assert not match(Command('aws dynamodb invalid', no_suggestions))