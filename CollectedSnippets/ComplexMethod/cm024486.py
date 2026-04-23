async def test_reading_broken_yaml_config(hass: HomeAssistant) -> None:
    """Test when known devices contains invalid data."""
    files = {
        "empty.yaml": "",
        "nodict.yaml": "100",
        "badkey.yaml": "@:\n  name: Device",
        "noname.yaml": "my_device:\n",
        "allok.yaml": "My Device:\n  name: Device",
        "oneok.yaml": "My Device!:\n  name: Device\nbad_device:\n  nme: Device",
    }
    args = {"hass": hass, "consider_home": timedelta(seconds=60)}
    with patch_yaml_files(files):
        assert await legacy.async_load_config("empty.yaml", **args) == []
        assert await legacy.async_load_config("nodict.yaml", **args) == []
        assert await legacy.async_load_config("noname.yaml", **args) == []
        assert await legacy.async_load_config("badkey.yaml", **args) == []

        res = await legacy.async_load_config("allok.yaml", **args)
        assert len(res) == 1
        assert res[0].name == "Device"
        assert res[0].dev_id == "my_device"

        res = await legacy.async_load_config("oneok.yaml", **args)
        assert len(res) == 1
        assert res[0].name == "Device"
        assert res[0].dev_id == "my_device"