def run_mock(mocker):
    return mocker.patch('pytest_docker_pexpect.docker.run', side_effect=run_side_effect)