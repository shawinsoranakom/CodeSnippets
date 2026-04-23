async def test_get_panels(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_http_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test get_panels command."""
    events = async_capture_events(hass, EVENT_PANELS_UPDATED)

    resp = await mock_http_client.get("/map")
    assert resp.status == HTTPStatus.NOT_FOUND

    async_register_built_in_panel(
        hass, "map", "Map", "mdi:tooltip-account", require_admin=True
    )

    resp = await mock_http_client.get("/map")
    assert resp.status == 200

    assert len(events) == 1

    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "get_panels"})

    msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["map"]["component_name"] == "map"
    assert msg["result"]["map"]["url_path"] == "map"
    assert msg["result"]["map"]["icon"] == "mdi:tooltip-account"
    assert msg["result"]["map"]["title"] == "Map"
    assert msg["result"]["map"]["require_admin"] is True
    assert msg["result"]["map"]["default_visible"] is True

    async_remove_panel(hass, "map")

    resp = await mock_http_client.get("/map")
    assert resp.status == HTTPStatus.NOT_FOUND

    assert len(events) == 2

    # Remove again, will warn but not trigger event
    async_remove_panel(hass, "map")
    assert "Removing unknown panel map" in caplog.text
    caplog.clear()

    # Remove again, without warning
    async_remove_panel(hass, "map", warn_if_unknown=False)
    assert "Removing unknown panel map" not in caplog.text