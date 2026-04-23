def test_no_domain_case6() -> None:
    """Test case 6 - include and exclude specified, with no domains."""
    incl_dom = {}
    incl_ent = {"binary_sensor.working"}
    excl_dom = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    assert testfilter("sensor.test") is False
    assert testfilter("sensor.notworking") is False
    assert testfilter("light.test") is False
    assert testfilter("light.ignoreme") is False
    assert testfilter("binary_sensor.working")
    assert testfilter("binary_sensor.another") is False
    assert testfilter("sun.sun") is False