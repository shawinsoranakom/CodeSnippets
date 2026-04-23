async def test_wlan_qr_code(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
    mock_websocket_message: WebsocketMessageMock,
) -> None:
    """Test the update_clients function when no clients are found."""
    assert len(hass.states.async_entity_ids(IMAGE_DOMAIN)) == 0

    ent_reg_entry = entity_registry.async_get("image.ssid_1_qr_code")
    assert ent_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    # Enable entity
    entity_registry.async_update_entity(
        entity_id="image.ssid_1_qr_code", disabled_by=None
    )
    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # Validate image
    client = await hass_client()
    resp = await client.get("/api/image_proxy/image.ssid_1_qr_code")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == snapshot

    # Update state object - same password - no change to state
    image_state_1 = hass.states.get("image.ssid_1_qr_code")
    mock_websocket_message(message=MessageKey.WLAN_CONF_UPDATED, data=WLAN)
    image_state_2 = hass.states.get("image.ssid_1_qr_code")
    assert image_state_1.state == image_state_2.state

    # Update state object - changed password - new state
    data = deepcopy(WLAN)
    data["x_passphrase"] = "new password"
    mock_websocket_message(message=MessageKey.WLAN_CONF_UPDATED, data=data)
    image_state_3 = hass.states.get("image.ssid_1_qr_code")
    assert image_state_1.state != image_state_3.state

    # Validate image
    client = await hass_client()
    resp = await client.get("/api/image_proxy/image.ssid_1_qr_code")
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == snapshot