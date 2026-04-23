async def test_events(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    load_config: MagicMock,
    event_payload: dict[str, Any],
    hass_client: ClientSessionGenerator,
    mock_jwt: MagicMock,
) -> None:
    """Test events."""
    load_config.return_value = {"my-desktop": SUBSCRIPTION_1}
    await async_setup_component(hass, "http", {})

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (state := hass.states.get("event.my_desktop")) is not None
    assert state.state == STATE_UNKNOWN

    client = await hass_client()

    mock_jwt.decode.return_value = {ATTR_TARGET: event_payload[ATTR_TARGET]}

    resp = await client.post(
        "/api/notify.html5/callback",
        json=event_payload,
        headers={AUTHORIZATION: "Bearer JWT"},
    )

    assert resp.status == HTTPStatus.OK

    assert (state := hass.states.get("event.my_desktop"))
    assert state.state == "1970-01-01T00:00:00.000+00:00"
    assert state.attributes.get("action") == event_payload.get(ATTR_ACTION)
    assert state.attributes.get("tag") == event_payload[ATTR_TAG]
    assert state.attributes.get("customKey") == event_payload[ATTR_DATA]["customKey"]