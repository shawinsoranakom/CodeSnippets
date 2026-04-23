async def test_v2_events(
    hass: HomeAssistant,
    mac_address: str,
    advertisement: BluetoothServiceInfoBleak,
    bind_key: str | None,
    result: list[dict[str, str]],
) -> None:
    """Test the different BTHome V2 events."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=mac_address,
        data={"bindkey": bind_key},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    inject_bluetooth_service_info(
        hass,
        advertisement,
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == len(result)

    for meas in result:
        state = hass.states.get(meas["entity"])
        attributes = state.attributes
        assert attributes[ATTR_FRIENDLY_NAME] == meas[ATTR_FRIENDLY_NAME]
        assert attributes[ATTR_EVENT_TYPE] == meas[ATTR_EVENT_TYPE]
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Ensure entities are restored
    for meas in result:
        state = hass.states.get(meas["entity"])
        assert state != STATE_UNAVAILABLE

    # Now inject again
    inject_bluetooth_service_info(
        hass,
        advertisement,
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == len(result)

    for meas in result:
        state = hass.states.get(meas["entity"])
        attributes = state.attributes
        assert attributes[ATTR_FRIENDLY_NAME] == meas[ATTR_FRIENDLY_NAME]
        assert attributes[ATTR_EVENT_TYPE] == meas[ATTR_EVENT_TYPE]
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()