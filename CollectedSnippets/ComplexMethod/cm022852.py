async def test_dashboard_from_yaml(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, url_path
) -> None:
    """Test we load lovelace dashboard config from yaml."""
    assert await async_setup_component(
        hass,
        "lovelace",
        {
            "lovelace": {
                "dashboards": {
                    "test-panel": {
                        "mode": "yaml",
                        "filename": "bla.yaml",
                        "title": "Test Panel",
                        "icon": "mdi:test-icon",
                        "show_in_sidebar": False,
                        "require_admin": True,
                    },
                    "test-panel-no-sidebar": {
                        "title": "Title No Sidebar",
                        "mode": "yaml",
                        "filename": "bla2.yaml",
                    },
                }
            }
        },
    )
    assert hass.data[frontend.DATA_PANELS]["test-panel"].config == {"mode": "yaml"}
    assert hass.data[frontend.DATA_PANELS]["test-panel-no-sidebar"].config == {
        "mode": "yaml"
    }

    client = await hass_ws_client(hass)

    # List dashboards
    await client.send_json({"id": 4, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 2
    with_sb, without_sb = response["result"]

    assert with_sb["mode"] == "yaml"
    assert with_sb["filename"] == "bla.yaml"
    assert with_sb["title"] == "Test Panel"
    assert with_sb["icon"] == "mdi:test-icon"
    assert with_sb["show_in_sidebar"] is False
    assert with_sb["require_admin"] is True
    assert with_sb["url_path"] == "test-panel"

    assert without_sb["mode"] == "yaml"
    assert without_sb["filename"] == "bla2.yaml"
    assert without_sb["show_in_sidebar"] is True
    assert without_sb["require_admin"] is False
    assert without_sb["url_path"] == "test-panel-no-sidebar"

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config", "url_path": url_path})
    response = await client.receive_json()
    assert not response["success"]

    assert response["error"]["code"] == "config_not_found"

    # Store new config not allowed
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/config/save",
            "config": {"yo": "hello"},
            "url_path": url_path,
        }
    )
    response = await client.receive_json()
    assert not response["success"]

    # Patch data
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo"},
    ):
        await client.send_json(
            {"id": 7, "type": "lovelace/config", "url_path": url_path}
        )
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo"}

    assert len(events) == 0

    # Fake new data to see we fire event
    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo2"},
    ):
        await client.send_json(
            {"id": 8, "type": "lovelace/config", "force": True, "url_path": url_path}
        )
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo2"}

    assert len(events) == 1