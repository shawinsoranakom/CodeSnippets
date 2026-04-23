def test_includes_only_with_glob_case_2() -> None:
    """If include specified, only pass if specified (Case 2)."""
    incl_dom = {"light", "sensor"}
    incl_glob = {"cover.*_window"}
    incl_ent = {"binary_sensor.working"}
    excl_dom = {}
    excl_glob = {}
    excl_ent = {}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    assert testfilter("sensor.test")
    assert testfilter("light.test")
    assert testfilter("cover.bedroom_window")
    assert testfilter("binary_sensor.working")
    assert testfilter("binary_sensor.notworking") is False
    assert testfilter("sun.sun") is False
    assert testfilter("cover.garage_door") is False