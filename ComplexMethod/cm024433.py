async def test_webhook_handle_get_zones(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that we can get zones properly."""
    # Zone is already loaded as part of the fixture,
    # so we just trigger a reload.
    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            ZONE_DOMAIN: [
                {
                    "name": "School",
                    "latitude": 32.8773367,
                    "longitude": -117.2494053,
                    "radius": 250,
                    "icon": "mdi:school",
                },
                {
                    "name": "Work",
                    "latitude": 33.8773367,
                    "longitude": -118.2494053,
                },
            ]
        },
    ):
        await hass.services.async_call(ZONE_DOMAIN, "reload", blocking=True)

    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[1]['webhook_id']}",
        json={"type": "get_zones"},
    )

    assert resp.status == HTTPStatus.OK

    json = await resp.json()
    assert len(json) == 3
    zones = sorted(json, key=lambda entry: entry["entity_id"])
    assert zones[0]["entity_id"] == "zone.home"

    assert zones[1]["entity_id"] == "zone.school"
    assert zones[1]["attributes"]["icon"] == "mdi:school"
    assert zones[1]["attributes"]["latitude"] == 32.8773367
    assert zones[1]["attributes"]["longitude"] == -117.2494053
    assert zones[1]["attributes"]["radius"] == 250

    assert zones[2]["entity_id"] == "zone.work"
    assert "icon" not in zones[2]["attributes"]
    assert zones[2]["attributes"]["latitude"] == 33.8773367
    assert zones[2]["attributes"]["longitude"] == -118.2494053