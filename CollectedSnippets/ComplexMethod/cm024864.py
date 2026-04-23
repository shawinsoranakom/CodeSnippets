def test_with_include_domain_glob_filtering_case4() -> None:
    """Test case 4 - include and exclude specified, both have domains and globs."""
    incl_dom = {"light"}
    incl_glob = {"*working"}
    incl_ent = {}
    excl_dom = {"binary_sensor"}
    excl_glob = {"*notworking"}
    excl_ent = {"light.ignoreme"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    assert testfilter("sensor.working")
    assert testfilter("sensor.notworking") is True  # include is stronger
    assert testfilter("light.test")
    assert testfilter("light.notworking") is True  # include is stronger
    assert testfilter("light.ignoreme") is False
    assert testfilter("binary_sensor.not_working") is True  # include is stronger
    assert testfilter("binary_sensor.another") is False
    assert testfilter("sun.sun") is False