def test_subrange():
    r = PortRange(50000, 60000)
    r.mark_reserved(50000)
    r.mark_reserved(50001)
    r.mark_reserved(50002)
    r.mark_reserved(50003)

    sr = r.subrange(end=50005)
    assert sr.as_range() == range(50000, 50006)

    assert sr.is_port_reserved(50000)
    assert sr.is_port_reserved(50001)
    assert sr.is_port_reserved(50002)
    assert sr.is_port_reserved(50003)
    assert not sr.is_port_reserved(50004)
    assert not sr.is_port_reserved(50005)

    sr.mark_reserved(50005)
    assert r.is_port_reserved(50005)