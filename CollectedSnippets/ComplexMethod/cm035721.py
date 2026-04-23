def test_init():
    handler = BitbucketIssueHandler(
        owner='test-workspace',
        repo='test-repo',
        token='test-token',
        username='test-user',
    )

    assert handler.owner == 'test-workspace'
    assert handler.repo == 'test-repo'
    assert handler.token == 'test-token'
    assert handler.username == 'test-user'
    assert handler.base_domain == 'bitbucket.org'
    assert handler.base_url == 'https://api.bitbucket.org/2.0'
    assert (
        handler.download_url
        == 'https://bitbucket.org/test-workspace/test-repo/get/master.zip'
    )
    assert handler.clone_url == 'https://bitbucket.org/test-workspace/test-repo.git'
    assert handler.headers == {
        'Authorization': 'Bearer test-token',
        'Accept': 'application/json',
    }