def test_map_set_del(m, key, value1):
    m[key] = value1
    l1 = len(m)
    del m[key]
    assert key not in m
    assert len(m) == l1 - 1