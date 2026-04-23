async def test_see_state(hass: HomeAssistant, yaml_devices: str) -> None:
    """Test device tracker see records state correctly."""
    assert await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
    await hass.async_block_till_done()

    params = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "dev_id": "some_device",
        "host_name": "example.com",
        "location_name": "Work",
        "gps": [0.3, 0.8],
        "gps_accuracy": 1,
        "battery": 100,
        "attributes": {"test": "test", "number": 1},
    }

    common.async_see(hass, **params)
    await hass.async_block_till_done()

    config = await legacy.async_load_config(yaml_devices, hass, timedelta(seconds=0))
    assert len(config) == 1

    state = hass.states.get("device_tracker.example_com")
    attrs = state.attributes
    assert state.state == "Work"
    assert state.object_id == "example_com"
    assert state.name == "example.com"
    assert attrs["friendly_name"] == "example.com"
    assert attrs["battery"] == 100
    assert attrs["latitude"] == 0.3
    assert attrs["longitude"] == 0.8
    assert attrs["test"] == "test"
    assert attrs["gps_accuracy"] == 1
    assert attrs["source_type"] == "gps"
    assert attrs["number"] == 1