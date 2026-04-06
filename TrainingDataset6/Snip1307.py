def test_match(build_misspelled_output):
    assert match(Command('go bulid', build_misspelled_output))