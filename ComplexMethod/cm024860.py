def test_excludes_only_with_glob_case_3() -> None:
    """If exclude specified, pass all but specified (Case 3)."""
    incl_dom = {}
    incl_glob = {}
    incl_ent = {}
    excl_dom = {"light", "sensor"}
    excl_glob = {"cover.*_window"}
    excl_ent = {"binary_sensor.working"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    assert testfilter("sensor.test") is False
    assert testfilter("light.test") is False
    assert testfilter("cover.bedroom_window") is False
    assert testfilter("binary_sensor.working") is False
    assert testfilter("binary_sensor.another")
    assert testfilter("sun.sun") is True
    assert testfilter("cover.garage_door")