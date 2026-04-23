async def test_websocket_list_dashboards(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test listing dashboards both storage + YAML."""
    assert await async_setup_component(
        hass,
        "lovelace",
        {
            "lovelace": {
                "dashboards": {
                    "test-panel-no-sidebar": {
                        "title": "Test YAML",
                        "mode": "yaml",
                        "filename": "bla.yaml",
                    },
                }
            }
        },
    )

    client = await hass_ws_client(hass)

    # Create a storage dashboard
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "title": "Test Storage",
        }
    )
    response = await client.receive_json()
    assert response["success"]

    # List dashboards
    await client.send_json({"id": 8, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 2
    with_sb, without_sb = response["result"]

    assert with_sb["mode"] == "yaml"
    assert with_sb["title"] == "Test YAML"
    assert with_sb["filename"] == "bla.yaml"
    assert with_sb["url_path"] == "test-panel-no-sidebar"

    assert without_sb["mode"] == "storage"
    assert without_sb["title"] == "Test Storage"
    assert without_sb["url_path"] == "created-url-path"