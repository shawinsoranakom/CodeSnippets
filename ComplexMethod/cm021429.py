async def test_duplicate_removal(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_daikin,
) -> None:
    """Test duplicate device removal."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=HOST,
        title=None,
        data={CONF_HOST: HOST, KEY_MAC: HOST},
    )
    config_entry.add_to_hass(hass)

    type(mock_daikin).mac = PropertyMock(return_value=HOST)
    type(mock_daikin).values = PropertyMock(return_value=INVALID_DATA)

    with patch(
        "homeassistant.components.daikin.async_migrate_unique_id", return_value=None
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

        assert config_entry.unique_id != MAC

        type(mock_daikin).mac = PropertyMock(return_value=MAC)
        type(mock_daikin).values = PropertyMock(return_value=DATA)

        assert await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()

        assert (
            device_registry.async_get_device({}, {(KEY_MAC, MAC)}).name
            == "DaikinAP00000"
        )

        assert device_registry.async_get_device({}, {(KEY_MAC, HOST)}).name is None

        assert entity_registry.async_get("climate.daikin_127_0_0_1").unique_id == HOST
        assert entity_registry.async_get("switch.zone_1").unique_id.startswith(HOST)

        assert entity_registry.async_get("climate.daikinap00000").unique_id == MAC
        assert entity_registry.async_get(
            "switch.daikinap00000_zone_1"
        ).unique_id.startswith(MAC)

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        device_registry.async_get_device({}, {(KEY_MAC, MAC)}).name == "DaikinAP00000"
    )

    assert entity_registry.async_get("climate.daikinap00000") is None
    assert entity_registry.async_get("switch.daikinap00000_zone_1") is None

    assert entity_registry.async_get("climate.daikin_127_0_0_1").unique_id == MAC
    assert entity_registry.async_get("switch.zone_1").unique_id.startswith(MAC)