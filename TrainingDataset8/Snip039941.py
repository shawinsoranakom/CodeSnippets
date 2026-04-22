def test_compact_idempotent(state):
    assert _compact_copy(state) == _compact_copy(_compact_copy(state))