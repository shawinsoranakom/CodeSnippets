def test_with_include_domain_exclude_glob_case4() -> None:
    """Test case 4 - include and exclude specified, with included domain but excluded by glob."""
    incl_dom = {"light", "sensor"}
    incl_ent = {"binary_sensor.working"}
    incl_glob = {}
    excl_dom = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    excl_glob = {"sensor.busted"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    assert testfilter("sensor.test")
    assert testfilter("sensor.busted") is False
    assert testfilter("sensor.notworking") is False
    assert testfilter("light.test")
    assert testfilter("light.ignoreme") is False
    assert testfilter("binary_sensor.working")
    assert testfilter("binary_sensor.another") is False
    assert testfilter("sun.sun") is False