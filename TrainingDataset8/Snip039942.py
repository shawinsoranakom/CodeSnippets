def test_compact_len(state):
    assert len(state) >= len(_compact_copy(state))