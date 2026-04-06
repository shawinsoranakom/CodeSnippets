def test_match(mistype_response):
    assert match(Command('conda lst', mistype_response))
    err_response = 'bash: codna: command not found'
    assert not match(Command('codna list', err_response))