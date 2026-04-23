async def test_update_panel(
    hass: HomeAssistant, ws_client: MockHAClientWebSocket
) -> None:
    """Test frontend/update_panel command."""
    # Verify initial state
    await ws_client.send_json({"id": 1, "type": "get_panels"})
    msg = await ws_client.receive_json()
    assert msg["result"]["light"]["icon"] == "mdi:lamps"
    assert msg["result"]["light"]["title"] == "light"
    assert msg["result"]["light"]["require_admin"] is False

    # Update the light panel
    events = async_capture_events(hass, EVENT_PANELS_UPDATED)
    await ws_client.send_json(
        {
            "id": 2,
            "type": "frontend/update_panel",
            "url_path": "light",
            "title": "My Lights",
            "icon": "mdi:lightbulb",
            "require_admin": True,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(events) == 1

    # Verify the panel was updated
    await ws_client.send_json({"id": 3, "type": "get_panels"})
    msg = await ws_client.receive_json()
    assert msg["result"]["light"]["icon"] == "mdi:lightbulb"
    assert msg["result"]["light"]["title"] == "My Lights"
    assert msg["result"]["light"]["require_admin"] is True