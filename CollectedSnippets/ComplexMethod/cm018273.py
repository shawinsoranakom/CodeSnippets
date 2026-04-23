async def test_image_entity(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    fc_class_mock,
    fh_class_mock,
) -> None:
    """Test image entity."""

    # setup component with image platform only
    with patch(
        "homeassistant.components.fritz.PLATFORMS",
        [Platform.IMAGE],
    ):
        entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)

    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    # test image entity is generated as expected
    states = hass.states.async_all(IMAGE_DOMAIN)
    assert len(states) == 1

    state = states[0]
    assert state.name == "Mock Title GuestWifi"
    assert state.entity_id == "image.mock_title_guestwifi"

    access_token = state.attributes["access_token"]
    assert state.attributes == {
        "access_token": access_token,
        "entity_picture": f"/api/image_proxy/image.mock_title_guestwifi?token={access_token}",
        "friendly_name": "Mock Title GuestWifi",
    }

    assert (state := entity_registry.async_get("image.mock_title_guestwifi"))
    assert state.unique_id == f"{MOCK_SERIAL_NUMBER}-guest_wifi_qr_code"

    # test image download
    client = await hass_client()
    resp = await client.get("/api/image_proxy/image.mock_title_guestwifi")
    assert resp.status == HTTPStatus.OK

    body = await resp.read()
    assert body == snapshot