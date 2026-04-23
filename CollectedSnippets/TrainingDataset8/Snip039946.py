def test_key_wid_lookup_equiv(state):
    k_wid_map = state._key_id_mapping
    for k, wid in k_wid_map.items():
        assert state[k] == state[wid]