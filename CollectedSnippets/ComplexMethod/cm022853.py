async def test_storage_dashboards(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test we load lovelace config from storage."""
    assert await async_setup_component(hass, "lovelace", {})

    # Default lovelace panel is registered for backward compatibility
    assert "lovelace" in hass.data[frontend.DATA_PANELS]

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    # Add a wrong dashboard (no hyphen)
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/dashboards/create",
            "url_path": "path",
            "title": "Test path without hyphen",
        }
    )
    response = await client.receive_json()
    assert not response["success"]

    # Add a dashboard
    await client.send_json(
        {
            "id": 7,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "require_admin": True,
            "title": "New Title",
            "icon": "mdi:map",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"]["require_admin"] is True
    assert response["result"]["title"] == "New Title"
    assert response["result"]["icon"] == "mdi:map"

    dashboard_id = response["result"]["id"]

    assert "created-url-path" in hass.data[frontend.DATA_PANELS]

    await client.send_json({"id": 8, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert response["result"][0]["mode"] == "storage"
    assert response["result"][0]["title"] == "New Title"
    assert response["result"][0]["icon"] == "mdi:map"
    assert response["result"][0]["show_in_sidebar"] is True
    assert response["result"][0]["require_admin"] is True

    # Fetch config
    await client.send_json(
        {"id": 9, "type": "lovelace/config", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "config_not_found"

    # Store new config
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    await client.send_json(
        {
            "id": 10,
            "type": "lovelace/config/save",
            "url_path": "created-url-path",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert hass_storage[dashboard.CONFIG_STORAGE_KEY.format(dashboard_id)]["data"] == {
        "config": {"yo": "hello"}
    }
    assert len(events) == 1
    assert events[0].data["url_path"] == "created-url-path"

    await client.send_json(
        {"id": 11, "type": "lovelace/config", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"yo": "hello"}

    # Update a dashboard
    await client.send_json(
        {
            "id": 12,
            "type": "lovelace/dashboards/update",
            "dashboard_id": dashboard_id,
            "require_admin": False,
            "icon": "mdi:updated",
            "show_in_sidebar": False,
            "title": "Updated Title",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"]["mode"] == "storage"
    assert response["result"]["url_path"] == "created-url-path"
    assert response["result"]["title"] == "Updated Title"
    assert response["result"]["icon"] == "mdi:updated"
    assert response["result"]["show_in_sidebar"] is False
    assert response["result"]["require_admin"] is False

    # List dashboards again and make sure we see latest config
    await client.send_json({"id": 13, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert response["result"][0]["mode"] == "storage"
    assert response["result"][0]["url_path"] == "created-url-path"
    assert response["result"][0]["title"] == "Updated Title"
    assert response["result"][0]["icon"] == "mdi:updated"
    assert response["result"][0]["show_in_sidebar"] is False
    assert response["result"][0]["require_admin"] is False

    # Add a wrong dashboard (missing title)
    await client.send_json(
        {
            "id": 14,
            "type": "lovelace/dashboards/create",
            "url_path": "path",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "invalid_format"

    # Add dashboard with existing url path
    await client.send_json(
        {
            "id": 15,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "title": "Another title",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    assert response["error"]["translation_key"] == "url_already_exists"
    assert response["error"]["translation_placeholders"]["url"] == "created-url-path"

    # Delete dashboards
    await client.send_json(
        {"id": 16, "type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id}
    )
    response = await client.receive_json()
    assert response["success"]

    assert "created-url-path" not in hass.data[frontend.DATA_PANELS]
    assert dashboard.CONFIG_STORAGE_KEY.format(dashboard_id) not in hass_storage