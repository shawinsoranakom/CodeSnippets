async def test_device_battery_level_reauth_required(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test API failure requires reauth."""
    aioclient_mock.get(
        DEVICES_API_URL,
        json=[DEVICE_RESPONSE_CHARGE_2],
    )
    assert await integration_setup()

    state = hass.states.get("sensor.charge_2_battery")
    assert state
    assert state.state == "Medium"

    # Request an update for the entity which will fail
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        DEVICES_API_URL,
        status=HTTPStatus.UNAUTHORIZED,
        json={
            "errors": [{"errorType": "invalid_grant"}],
        },
    )
    await async_update_entity(hass, "sensor.charge_2_battery")
    await hass.async_block_till_done()

    state = hass.states.get("sensor.charge_2_battery")
    assert state
    assert state.state == "unavailable"

    # Verify that reauth is required
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"