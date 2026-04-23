async def test_channel_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_device: RokuDevice,
    mock_roku: MagicMock,
) -> None:
    """Test the creation and values of the Roku selects."""
    state = hass.states.get("select.58_onn_roku_tv_channel")
    assert state
    assert state.attributes.get(ATTR_OPTIONS) == [
        "99.1",
        "QVC (1.3)",
        "WhatsOn (1.1)",
        "getTV (14.3)",
    ]
    assert state.state == "getTV (14.3)"

    entry = entity_registry.async_get("select.58_onn_roku_tv_channel")
    assert entry
    assert entry.unique_id == "YN00H5555555_channel"

    # channel name
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.58_onn_roku_tv_channel",
            ATTR_OPTION: "WhatsOn (1.1)",
        },
        blocking=True,
    )

    assert mock_roku.tune.call_count == 1
    mock_roku.tune.assert_called_with("1.1")
    mock_device.channel = mock_device.channels[0]

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    state = hass.states.get("select.58_onn_roku_tv_channel")
    assert state
    assert state.state == "WhatsOn (1.1)"

    # channel number
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.58_onn_roku_tv_channel",
            ATTR_OPTION: "99.1",
        },
        blocking=True,
    )

    assert mock_roku.tune.call_count == 2
    mock_roku.tune.assert_called_with("99.1")
    mock_device.channel = mock_device.channels[3]

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    state = hass.states.get("select.58_onn_roku_tv_channel")
    assert state
    assert state.state == "99.1"