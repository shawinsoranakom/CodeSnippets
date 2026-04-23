async def test_guest_wifi_qr(
    hass: HomeAssistant,
    mock_device: MockDevice,
    entity_registry: er.EntityRegistry,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test showing a QR code of the guest wifi credentials."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    entity_id = f"{IMAGE_DOMAIN}.{device_name}_guest_wi_fi_credentials_as_qr_code"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.name == "Mock Title Guest Wi-Fi credentials as QR code"
    assert state.state == dt_util.utcnow().isoformat()
    assert entity_registry.async_get(entity_id) == snapshot

    client = await hass_client()
    resp = await client.get(f"/api/image_proxy/{entity_id}")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == snapshot

    # Emulate device failure
    mock_device.device.async_get_wifi_guest_access.side_effect = DeviceUnavailable()
    freezer.tick(SHORT_UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Emulate state change
    mock_device.device.async_get_wifi_guest_access = AsyncMock(
        return_value=GUEST_WIFI_CHANGED
    )
    freezer.tick(SHORT_UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == dt_util.utcnow().isoformat()

    client = await hass_client()
    resp = await client.get(f"/api/image_proxy/{entity_id}")
    assert resp.status == HTTPStatus.OK
    assert await resp.read() != body