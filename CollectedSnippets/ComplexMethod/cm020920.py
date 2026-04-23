async def test_option_ssid_filter(
    hass: HomeAssistant,
    mock_websocket_message,
    config_entry_factory: ConfigEntryFactoryType,
    client_payload: list[dict[str, Any]],
) -> None:
    """Test the SSID filter works.

    Client will travel from a supported SSID to an unsupported ssid.
    Client on SSID2 will be removed on change of options.
    """
    client_payload += [
        WIRELESS_CLIENT_1 | {"last_seen": dt_util.as_timestamp(dt_util.utcnow())},
        {
            "essid": "ssid2",
            "hostname": "client_on_ssid2",
            "is_wired": False,
            "last_seen": 1562600145,
            "mac": "00:00:00:00:00:02",
        },
    ]
    config_entry = await config_entry_factory()

    assert len(hass.states.async_entity_ids(TRACKER_DOMAIN)) == 2
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME
    assert hass.states.get("device_tracker.client_on_ssid2").state == STATE_NOT_HOME

    # Setting SSID filter will remove clients outside of filter
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_SSID_FILTER: ["ssid"]}
    )
    await hass.async_block_till_done()

    # Not affected by SSID filter
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME

    # Removed due to SSID filter
    assert not hass.states.get("device_tracker.client_on_ssid2")

    # Roams to SSID outside of filter
    ws_client_1 = client_payload[0] | {"essid": "other_ssid"}
    mock_websocket_message(message=MessageKey.CLIENT, data=ws_client_1)

    # Data update while SSID filter is in effect shouldn't create the client
    client_on_ssid2 = client_payload[1] | {
        "last_seen": dt_util.as_timestamp(dt_util.utcnow())
    }
    mock_websocket_message(message=MessageKey.CLIENT, data=client_on_ssid2)
    await hass.async_block_till_done()

    new_time = dt_util.utcnow() + timedelta(seconds=(DEFAULT_DETECTION_TIME + 1))
    with freeze_time(new_time):
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()

    # SSID filter marks client as away
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME

    # SSID still outside of filter
    assert not hass.states.get("device_tracker.client_on_ssid2")

    # Remove SSID filter
    hass.config_entries.async_update_entry(config_entry, options={CONF_SSID_FILTER: []})
    await hass.async_block_till_done()

    ws_client_1["last_seen"] += 1
    client_on_ssid2["last_seen"] += 1
    mock_websocket_message(
        message=MessageKey.CLIENT, data=[ws_client_1, client_on_ssid2]
    )
    await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME
    assert hass.states.get("device_tracker.client_on_ssid2").state == STATE_HOME

    # Time pass to mark client as away
    new_time += timedelta(seconds=(DEFAULT_DETECTION_TIME + 1))
    with freeze_time(new_time):
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME

    client_on_ssid2["last_seen"] += 1
    mock_websocket_message(message=MessageKey.CLIENT, data=client_on_ssid2)
    await hass.async_block_till_done()

    # Client won't go away until after next update
    assert hass.states.get("device_tracker.client_on_ssid2").state == STATE_HOME

    # Trigger update to get client marked as away
    client_on_ssid2["last_seen"] += 1
    mock_websocket_message(message=MessageKey.CLIENT, data=client_on_ssid2)
    await hass.async_block_till_done()

    new_time += timedelta(seconds=DEFAULT_DETECTION_TIME)
    with freeze_time(new_time):
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()

    assert hass.states.get("device_tracker.client_on_ssid2").state == STATE_NOT_HOME