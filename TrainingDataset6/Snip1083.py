def test_get_new_command(mistype_response):
    assert (get_new_command(Command('conda lst', mistype_response)) == ['conda list'])