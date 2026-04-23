def test_map_set_set(m, key, value1, value2):
    m[key] = value1
    l1 = len(m)
    m[key] = value2
    assert m[key] == value2
    assert len(m) == l1