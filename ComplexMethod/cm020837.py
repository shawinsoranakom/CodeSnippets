async def test_labs_feature_toggle(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that snapshots can be toggled via labs feature."""
    aioclient_mock.post(SNAPSHOT_ENDPOINT_URL, status=200, json={})

    assert await async_setup_component(hass, "labs", {})
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=25))
    await hass.async_block_till_done()

    assert len(aioclient_mock.mock_calls) == 0

    await async_update_preview_feature(hass, DOMAIN, LABS_SNAPSHOT_FEATURE, True)

    assert hass_storage[STORAGE_KEY]["data"]["preferences"]["snapshots"] is True

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=25))
    await hass.async_block_till_done()

    assert any(
        str(call[1]) == SNAPSHOT_ENDPOINT_URL for call in aioclient_mock.mock_calls
    )

    aioclient_mock.clear_requests()

    await async_update_preview_feature(hass, DOMAIN, LABS_SNAPSHOT_FEATURE, False)

    assert hass_storage[STORAGE_KEY]["data"]["preferences"]["snapshots"] is False

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=25))
    await hass.async_block_till_done()

    assert len(aioclient_mock.mock_calls) == 0