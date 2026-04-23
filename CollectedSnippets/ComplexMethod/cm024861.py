def test_with_include_domain_case4() -> None:
    """Test case 4 - include and exclude specified, with included domain."""
    incl_dom = {"light", "sensor"}
    incl_ent = {"binary_sensor.working"}
    excl_dom = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    assert testfilter("sensor.test")
    assert testfilter("sensor.notworking") is False
    assert testfilter("light.test")
    assert testfilter("light.ignoreme") is False
    assert testfilter("binary_sensor.working")
    assert testfilter("binary_sensor.another") is False
    assert testfilter("sun.sun") is False