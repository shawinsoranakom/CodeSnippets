async def test_image_update(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
    mock_vodafone_station_router: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test image update."""

    entity_id = f"image.vodafone_station_{TEST_SERIAL_NUMBER}_guest_network"

    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED

    client = await hass_client()
    resp = await client.get(f"/api/image_proxy/{entity_id}")
    assert resp.status == HTTPStatus.OK

    resp_body = await resp.read()

    assert (state := hass.states.get(entity_id))
    assert state.state == "2023-12-02T13:00:00+00:00"

    mock_vodafone_station_router.get_wifi_data.return_value = {
        WIFI_DATA: {
            "guest": {
                "on": 1,
                "ssid": "Wifi-Guest",
                "qr_code": BytesIO(b"fake-qr-code-guest-updated"),
            },
            "guest_5g": {
                "on": 0,
                "ssid": "Wifi-Guest-5Ghz",
                "qr_code": BytesIO(b"fake-qr-code-guest-5ghz-updated"),
            },
        }
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    new_time = dt_util.utcnow()

    resp = await client.get(f"/api/image_proxy/{entity_id}")
    assert resp.status == HTTPStatus.OK

    resp_body_new = await resp.read()
    assert resp_body != resp_body_new

    assert (state := hass.states.get(entity_id))
    assert state.state == new_time.isoformat()