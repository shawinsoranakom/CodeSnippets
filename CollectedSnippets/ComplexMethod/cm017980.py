def test_extract_platform_integrations() -> None:
    """Test extract_platform_integrations."""
    config = OrderedDict(
        [
            (b"zone", {"platform": "not str"}),
            ("zone", {"platform": "hello"}),
            ("switch", {"platform": ["un", "hash", "able"]}),
            ("zonex", []),
            ("zoney", ""),
            ("notzone", {"platform": "nothello"}),
            ("zoner", None),
            ("zone Hallo", [1, {"platform": "hello 2"}]),
            ("zone 100", None),
            ("i n v a-@@", None),
            ("i n v a-@@", {"platform": "hello"}),
            ("zoneq", "pig"),
            ("zoneempty", {"platform": ""}),
        ]
    )
    assert config_util.extract_platform_integrations(config, {"zone"}) == {
        "zone": {"hello", "hello 2"}
    }
    assert config_util.extract_platform_integrations(config, {"switch"}) == {}
    assert config_util.extract_platform_integrations(config, {"zonex"}) == {}
    assert config_util.extract_platform_integrations(config, {"zoney"}) == {}
    assert config_util.extract_platform_integrations(
        config, {"zone", "not_valid", "notzone"}
    ) == {"zone": {"hello 2", "hello"}, "notzone": {"nothello"}}
    assert config_util.extract_platform_integrations(config, {"zoneq"}) == {}
    assert config_util.extract_platform_integrations(config, {"zoneempty"}) == {}