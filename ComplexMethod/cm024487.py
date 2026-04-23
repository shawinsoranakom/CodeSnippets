async def test_reading_yaml_config(hass: HomeAssistant, yaml_devices: str) -> None:
    """Test the rendering of the YAML configuration."""
    dev_id = "test"
    device = legacy.Device(
        hass,
        timedelta(seconds=180),
        True,
        dev_id,
        "AB:CD:EF:GH:IJ",
        "Test name",
        picture="http://test.picture",
        icon="mdi:kettle",
    )
    await hass.async_add_executor_job(
        legacy.update_config, yaml_devices, dev_id, device
    )
    loaded_config = None
    original_async_load_config = legacy.async_load_config

    async def capture_load_config(*args, **kwargs):
        nonlocal loaded_config
        loaded_config = await original_async_load_config(*args, **kwargs)
        return loaded_config

    with patch(
        "homeassistant.components.device_tracker.legacy.async_load_config",
        capture_load_config,
    ):
        assert await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        await hass.async_block_till_done()
    config = loaded_config[0]
    assert device.dev_id == config.dev_id
    assert device.track == config.track
    assert device.mac == config.mac
    assert device.config_picture == config.config_picture
    assert device.consider_home == config.consider_home
    assert device.icon == config.icon
    assert f"test.{device_tracker.DOMAIN}" in hass.config.components