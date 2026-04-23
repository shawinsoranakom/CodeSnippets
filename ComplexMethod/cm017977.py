async def test_merge(merge_log_err: MagicMock, hass: HomeAssistant) -> None:
    """Test if we can merge packages."""
    packages = {
        "pack_dict": {"input_boolean": {"ib1": None}},
        "pack_11": {"input_select": {"is1": None}},
        "pack_list": {"light": {"platform": "test"}},
        "pack_list2": {"light": [{"platform": "test"}]},
        "pack_none": {"wake_on_lan": None},
        "pack_special": {
            "automation": [{"some": "yay"}],
            "script": {"a_script": "yay"},
            "template": [{"some": "yay"}],
        },
    }
    config = {
        HOMEASSISTANT_DOMAIN: {CONF_PACKAGES: packages},
        "input_boolean": {"ib2": None},
        "light": {"platform": "test"},
        "automation": [],
        "script": {},
        "template": [],
    }
    await config_util.merge_packages_config(hass, config, packages)

    assert merge_log_err.call_count == 0
    assert len(config) == 8
    assert len(config["input_boolean"]) == 2
    assert len(config["input_select"]) == 1
    assert len(config["light"]) == 3
    assert len(config["automation"]) == 1
    assert len(config["script"]) == 1
    assert len(config["template"]) == 1
    assert isinstance(config["wake_on_lan"], OrderedDict)