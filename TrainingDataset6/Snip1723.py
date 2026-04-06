def test_get_all_matched_commands(stderr, result):
    assert list(get_all_matched_commands(stderr)) == result