def test_match(mistype_response):
    assert match(Command('git lfs evn', mistype_response))
    err_response = 'bash: git: command not found'
    assert not match(Command('git lfs env', err_response))
    assert not match(Command('docker lfs env', mistype_response))