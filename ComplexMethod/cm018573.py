async def test_zeroconf_sleeping_device_attempts_configure_ws_disabled(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test zeroconf discovery configures a sleeping device outbound websocket when its disabled."""
    monkeypatch.setattr(mock_rpc_device, "connected", False)
    monkeypatch.setattr(mock_rpc_device, "initialized", False)
    monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
    monkeypatch.setitem(
        mock_rpc_device.config, "ws", {"enable": False, "server": "ws://oldha"}
    )
    entry = MockConfigEntry(
        domain="shelly",
        unique_id="AABBCCDDEEFF",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_GEN: 2,
            CONF_SLEEP_PERIOD: 1000,
            CONF_MODEL: MODEL_1,
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    mock_rpc_device.mock_disconnected()
    await hass.async_block_till_done()

    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "online, resuming setup" in caplog.text
    assert len(mock_rpc_device.initialize.mock_calls) == 1

    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={"mac": "AABBCCDDEEFF", "type": MODEL_1, "auth": False},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    assert mock_rpc_device.update_outbound_websocket.mock_calls == []

    monkeypatch.setattr(mock_rpc_device, "connected", True)
    monkeypatch.setattr(mock_rpc_device, "initialized", True)
    mock_rpc_device.mock_initialized()
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=ENTRY_RELOAD_COOLDOWN)
    )
    await hass.async_block_till_done()
    assert "device did not update" not in caplog.text

    monkeypatch.setattr(mock_rpc_device, "connected", False)
    mock_rpc_device.mock_disconnected()
    assert mock_rpc_device.update_outbound_websocket.mock_calls == [
        call("ws://10.10.10.10:8123/api/shelly/ws")
    ]