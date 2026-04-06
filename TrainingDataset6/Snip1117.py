def test_not_docker_command():
    err_response = """Error response from daemon: conflict: unable to delete cd809b04b6ff (cannot be forced) - image is being used by running container e5e2591040d1"""
    assert not match(Command('git image rm -f cd809b04b6ff', err_response))