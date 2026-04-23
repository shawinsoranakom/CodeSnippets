async def test_unique_id_migrate(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_daikin,
) -> None:
    """Test unique id migration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=HOST,
        title=None,
        data={CONF_HOST: HOST, KEY_MAC: HOST},
    )
    config_entry.add_to_hass(hass)

    type(mock_daikin).mac = PropertyMock(return_value=HOST)
    type(mock_daikin).values = PropertyMock(return_value=INVALID_DATA)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.unique_id == HOST

    assert device_registry.async_get_device(connections={(KEY_MAC, HOST)}).name is None

    entity = entity_registry.async_get("climate.daikin_127_0_0_1")
    assert entity.unique_id == HOST
    assert update_unique_id(entity, MAC) is not None

    assert entity_registry.async_get("switch.zone_1").unique_id.startswith(HOST)

    type(mock_daikin).mac = PropertyMock(return_value=MAC)
    type(mock_daikin).values = PropertyMock(return_value=DATA)

    assert config_entry.unique_id != MAC

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.unique_id == MAC

    assert (
        device_registry.async_get_device(connections={(KEY_MAC, MAC)}).name
        == "DaikinAP00000"
    )

    entity = entity_registry.async_get("climate.daikin_127_0_0_1")
    assert entity.unique_id == MAC
    assert update_unique_id(entity, MAC) is None

    assert entity_registry.async_get("switch.zone_1").unique_id.startswith(MAC)