async def test_html5_send_message(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    webpush_async: AsyncMock,
    load_config: MagicMock,
    service_data: dict[str, Any],
    expected_payload: dict[str, Any],
    expected_ttl: int,
    expected_headers: dict[str, Any] | None,
) -> None:
    """Test sending a message via html5.send_message action."""
    load_config.return_value = {"my-desktop": SUBSCRIPTION_1}

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    state = hass.states.get("notify.my_desktop")
    assert state
    assert state.state == STATE_UNKNOWN

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        {ATTR_ENTITY_ID: "notify.my_desktop", ATTR_TITLE: "Hello", **service_data},
        blocking=True,
    )

    state = hass.states.get("notify.my_desktop")
    assert state
    assert state.state == "2009-02-13T23:31:30+00:00"

    webpush_async.assert_awaited_once()
    assert webpush_async.await_args
    _, payload, _, _ = webpush_async.await_args.args
    assert json.loads(payload) == {
        "title": "Hello",
        "tag": "12345678-1234-5678-1234-567812345678",
        "timestamp": 1234567890000,
        "data": {"jwt": "JWT"},
        **expected_payload,
    }

    assert webpush_async.await_args.kwargs["ttl"] == expected_ttl
    assert webpush_async.await_args.kwargs["headers"] == expected_headers