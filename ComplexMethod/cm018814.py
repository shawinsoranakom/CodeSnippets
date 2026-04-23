async def test_image_entity(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_vodafone_station_router: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test image entity."""

    entity_id = f"image.vodafone_station_{TEST_SERIAL_NUMBER}_guest_network"

    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # test image entities are generated as expected
    states = hass.states.async_all(IMAGE_DOMAIN)
    assert len(states) == 2

    state = states[0]
    assert state.name == f"Vodafone Station ({TEST_SERIAL_NUMBER}) Guest network"
    assert state.entity_id == entity_id

    access_token = state.attributes["access_token"]
    assert state.attributes == {
        "access_token": access_token,
        "entity_picture": f"/api/image_proxy/{entity_id}?token={access_token}",
        "friendly_name": f"Vodafone Station ({TEST_SERIAL_NUMBER}) Guest network",
    }

    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry is not None
    assert entity_entry.unique_id == f"{TEST_SERIAL_NUMBER}-guest-qr-code"

    # test image download
    client = await hass_client()
    resp = await client.get(f"/api/image_proxy/{entity_id}")
    assert resp.status == HTTPStatus.OK

    body = await resp.read()
    assert body == snapshot

    assert (state := hass.states.async_all(IMAGE_DOMAIN)[0])
    assert state.state == "2023-12-02T13:00:00+00:00"