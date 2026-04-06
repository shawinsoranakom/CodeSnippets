def test_not_match():
    err_response = 'bash: docker: command not found'
    assert not match(Command('docker image rm -f cd809b04b6ff', err_response))