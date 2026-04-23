async def test_websocket_update_orientation_prefs(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test updating camera preferences."""
    await async_setup_component(hass, "homeassistant", {})

    client = await hass_ws_client(hass)

    # Try sending orientation update for entity not in entity registry
    await client.send_json(
        {
            "id": 10,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_uniquecamera",
            "orientation": 3,
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "update_failed"

    assert not entity_registry.async_get("camera.demo_uniquecamera")
    # Since we don't have a unique id, we need to create a registry entry
    entity_registry.async_get_or_create(DOMAIN, "demo", "uniquecamera")
    entity_registry.async_update_entity_options(
        "camera.demo_uniquecamera",
        DOMAIN,
        {},
    )

    await client.send_json(
        {
            "id": 11,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_uniquecamera",
            "orientation": 3,
        }
    )
    response = await client.receive_json()
    assert response["success"]

    er_camera_prefs = entity_registry.async_get("camera.demo_uniquecamera").options[
        DOMAIN
    ]
    assert er_camera_prefs[PREF_ORIENTATION] == camera.Orientation.ROTATE_180
    assert response["result"][PREF_ORIENTATION] == er_camera_prefs[PREF_ORIENTATION]
    # Check that the preference was saved
    await client.send_json(
        {"id": 12, "type": "camera/get_prefs", "entity_id": "camera.demo_uniquecamera"}
    )
    msg = await client.receive_json()
    # orientation entry for this camera should have been added
    assert msg["result"]["orientation"] == camera.Orientation.ROTATE_180