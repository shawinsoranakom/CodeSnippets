async def test_system_health(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test system health."""
    aioclient_mock.get(f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}", text="")

    hass.config.components.add(DOMAIN)
    assert await async_setup_component(hass, "system_health", {})
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=MOCK_ENTRY_ID,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}"},
        unique_id=MOCK_UUID,
        state=ConfigEntryState.LOADED,
    )
    entry.add_to_hass(hass)

    isy_data = Mock(
        root=Mock(
            connected=True,
            websocket=Mock(
                last_heartbeat=MOCK_HEARTBEAT,
                status=MOCK_CONNECTED,
            ),
        )
    )
    entry.runtime_data = isy_data

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info["host_reachable"] == "ok"
    assert info["device_connected"]
    assert info["last_heartbeat"] == MOCK_HEARTBEAT
    assert info["websocket_status"] == MOCK_CONNECTED