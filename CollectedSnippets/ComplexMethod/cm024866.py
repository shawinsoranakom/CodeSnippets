def test_with_include_glob_filtering_case4a_include_strong() -> None:
    """Test case 4 - include and exclude specified, both have globs, and a specifically included entity."""
    incl_dom = {}
    incl_glob = {"*working"}
    incl_ent = {"binary_sensor.specificly_included"}
    excl_dom = {}
    excl_glob = {"*broken", "*notworking", "binary_sensor.*"}
    excl_ent = {"light.ignoreme"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    assert testfilter("sensor.working") is True
    assert testfilter("sensor.notworking") is True  # include is stronger
    assert testfilter("sensor.broken") is False
    assert testfilter("light.test") is False
    assert testfilter("light.notworking") is True  # include is stronger
    assert testfilter("light.ignoreme") is False
    assert testfilter("binary_sensor.not_working") is True  # include is stronger
    assert testfilter("binary_sensor.another") is False
    assert testfilter("binary_sensor.specificly_included") is True
    assert testfilter("sun.sun") is False