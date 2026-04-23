async def test_rpc_reload_with_invalid_auth(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC when InvalidAuthError is raising during config entry reload."""
    with patch(
        "homeassistant.components.shelly.coordinator.async_stop_scanner",
        side_effect=[None, InvalidAuthError, None],
    ):
        entry = await init_integration(hass, 2)

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "data": [],
                        "event": "config_changed",
                        "id": 1,
                        "ts": 1668522399.2,
                    },
                    {
                        "data": [],
                        "id": 2,
                        "ts": 1668522399.2,
                    },
                ],
                "ts": 1668522399.2,
            },
        )

        await hass.async_block_till_done()

        # Move time to generate reconnect
        freezer.tick(timedelta(seconds=RPC_RECONNECT_INTERVAL))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == entry.entry_id