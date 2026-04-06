def test_match():
    err_response = """Error response from daemon: conflict: unable to delete cd809b04b6ff (cannot be forced) - image is being used by running container e5e2591040d1"""
    assert match(Command('docker image rm -f cd809b04b6ff', err_response))