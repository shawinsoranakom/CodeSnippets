async def test_services(
    hass: HomeAssistant, mock_config_entry: tuple[MockConfigEntry, list[ValveEntity]]
) -> None:
    """Test the provided services."""
    config_entry = mock_config_entry[0]
    ent1, ent2 = mock_config_entry[1]

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Test init all valves should be open
    assert is_open(hass, ent1)
    assert is_open(hass, ent2, 50)

    # call basic toggle services
    await call_service(hass, SERVICE_TOGGLE, ent1)
    await call_service(hass, SERVICE_TOGGLE, ent2)
    await hass.async_block_till_done()

    # entities without stop should be closed and with stop should be closing
    assert is_closed(hass, ent1)
    assert is_closing(hass, ent2, 50)
    ent2.finish_movement()
    assert is_closed(hass, ent2, 0)

    # call basic toggle services and set different valve position states
    await call_service(hass, SERVICE_TOGGLE, ent1)
    await call_service(hass, SERVICE_TOGGLE, ent2)
    await hass.async_block_till_done()

    # entities should be in correct state depending on the SUPPORT_STOP feature and valve position
    assert is_open(hass, ent1)
    assert is_opening(hass, ent2, 0, True)
    ent2.finish_movement()
    assert is_open(hass, ent2, 100)

    # call basic toggle services
    await call_service(hass, SERVICE_TOGGLE, ent1)
    await call_service(hass, SERVICE_TOGGLE, ent2)
    await hass.async_block_till_done()

    # entities should be in correct state depending on the SUPPORT_STOP feature and valve position
    assert is_closed(hass, ent1)
    assert not is_opening(hass, ent2)
    assert not is_closed(hass, ent2, 100)
    assert is_closing(hass, ent2, 100)
    ent2.finish_movement()
    assert is_closed(hass, ent2, 0)

    await call_service(hass, SERVICE_SET_VALVE_POSITION, ent2, 50)
    await hass.async_block_till_done()
    assert is_opening(hass, ent2, 0, True)
    ent2.finish_movement()
    assert is_open(hass, ent2, 50)