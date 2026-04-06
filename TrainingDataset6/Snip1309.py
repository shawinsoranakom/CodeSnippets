def test_get_new_command(build_misspelled_output):
    assert get_new_command(Command('go bulid', build_misspelled_output)) == 'go build'