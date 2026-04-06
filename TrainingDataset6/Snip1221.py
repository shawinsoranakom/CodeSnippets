def test_get_new_command(mistype_response):
    assert (get_new_command(Command('git lfs evn', mistype_response))
            == ['git lfs env', 'git lfs ext'])