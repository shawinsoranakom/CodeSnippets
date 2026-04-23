async def test_update_panel_toggle_show_in_sidebar(
    hass: HomeAssistant, ws_client: MockHAClientWebSocket
) -> None:
    """Test that show_in_sidebar is returned without altering title and icon."""
    # Verify initial state has title and icon
    await ws_client.send_json({"id": 1, "type": "get_panels"})
    msg = await ws_client.receive_json()
    assert msg["result"]["light"]["title"] == "light"
    assert msg["result"]["light"]["icon"] == "mdi:lamps"
    assert msg["result"]["light"]["show_in_sidebar"] is False

    # Show in sidebar
    await ws_client.send_json(
        {
            "id": 2,
            "type": "frontend/update_panel",
            "url_path": "light",
            "show_in_sidebar": True,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    # Title and icon should remain unchanged and show_in_sidebar should be True
    await ws_client.send_json({"id": 3, "type": "get_panels"})
    msg = await ws_client.receive_json()
    assert msg["result"]["light"]["title"] == "light"
    assert msg["result"]["light"]["icon"] == "mdi:lamps"
    assert msg["result"]["light"]["show_in_sidebar"] is True

    # Reset show_in_sidebar to panel default
    await ws_client.send_json(
        {
            "id": 4,
            "type": "frontend/update_panel",
            "url_path": "light",
            "show_in_sidebar": None,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    # show_in_sidebar should be restored to built-in default
    await ws_client.send_json({"id": 5, "type": "get_panels"})
    msg = await ws_client.receive_json()
    assert msg["result"]["light"]["title"] == "light"
    assert msg["result"]["light"]["icon"] == "mdi:lamps"
    assert msg["result"]["light"]["show_in_sidebar"] is False