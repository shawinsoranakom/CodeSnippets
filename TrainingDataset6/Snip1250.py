def test_match_bitbucket(output_bitbucket):
    assert not match(Command('git push origin', output_bitbucket))