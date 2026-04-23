async def test_hddtemp_multiple_disks(hass: HomeAssistant, telnetmock) -> None:
    """Test hddtemp multiple disk configuration."""
    assert await async_setup_component(hass, "sensor", VALID_CONFIG_MULTIPLE_DISKS)
    await hass.async_block_till_done()

    for sensor in (
        "sensor.hd_temperature_dev_sda1",
        "sensor.hd_temperature_dev_sdb1",
        "sensor.hd_temperature_dev_sdc1",
    ):
        state = hass.states.get(sensor)

        reference = REFERENCE[state.attributes.get("device")]

        assert state.state == reference["temperature"]
        assert state.attributes.get("device") == reference["device"]
        assert state.attributes.get("model") == reference["model"]
        assert (
            state.attributes.get("unit_of_measurement")
            == reference["unit_of_measurement"]
        )
        assert (
            state.attributes.get("friendly_name")
            == f"HD Temperature {reference['device']}"
        )