async def test_device_availability(
    hass: HomeAssistant,
    mock_govee_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test device availability tracks lastseen against DEVICE_TIMEOUT.

    Walks the full timeline in a single fixture: stays available below the
    timeout, goes unavailable past it, and recovers when a status response
    refreshes ``lastseen``.
    """
    device = GoveeDevice(
        controller=mock_govee_api,
        ip="192.168.1.100",
        fingerprint="asdawdqwdqwd",
        sku="H615A",
        capabilities=DEFAULT_CAPABILITIES,
    )
    mock_govee_api.devices = [device]

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("light.H615A")
    assert state is not None
    assert state.state == STATE_OFF

    # Advance but stay below DEVICE_TIMEOUT: the device must remain available
    # even though no status responses have arrived.
    freezer.tick(DEVICE_TIMEOUT - SCAN_INTERVAL)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    state = hass.states.get("light.H615A")
    assert state is not None
    assert state.state == STATE_OFF

    # Advance past DEVICE_TIMEOUT: the device should go unavailable.
    freezer.tick(SCAN_INTERVAL * 2)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    state = hass.states.get("light.H615A")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # A status response refreshes lastseen and fires the entity callback, so
    # the device recovers without waiting for another coordinator poll.
    device.update(_status_response())
    await hass.async_block_till_done()

    state = hass.states.get("light.H615A")
    assert state is not None
    assert state.state == STATE_OFF