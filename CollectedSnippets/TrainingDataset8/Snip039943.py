def test_compact_presence(state):
    assert _sorted_items(state) == _sorted_items(_compact_copy(state))