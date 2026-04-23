async def test_connection_test(
    hass: HomeAssistant,
    init_components: ConfigEntry,
    entity: MockAssistSatellite,
    hass_ws_client: WebSocketGenerator,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test connection test."""
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id(
        {
            "type": "assist_satellite/test_connection",
            "entity_id": ENTITY_ID,
        }
    )

    for _ in range(3):
        await asyncio.sleep(0)

    assert len(entity.announcements) == 1
    assert entity.announcements[0].message == ""
    assert entity.announcements[0].preannounce_media_id is None
    announcement_media_id = entity.announcements[0].media_id
    hass_url = "http://10.10.10.10:8123"
    assert announcement_media_id.startswith(
        f"{hass_url}/api/assist_satellite/connection_test/"
    )

    # Fake satellite fetches the URL
    client = await hass_client()
    resp = await client.get(announcement_media_id[len(hass_url) :])
    assert resp.status == HTTPStatus.OK

    response = await ws_client.receive_json()
    assert response["success"]
    assert response["result"] == {"status": "success"}