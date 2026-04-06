def test_get_new_command():
    assert get_new_command(Command('docker build -t artifactory:9090/foo/bar:fdb7c6d .', '')) == 'docker login && docker build -t artifactory:9090/foo/bar:fdb7c6d .'
    assert get_new_command(Command('docker push artifactory:9090/foo/bar:fdb7c6d', '')) == 'docker login && docker push artifactory:9090/foo/bar:fdb7c6d'