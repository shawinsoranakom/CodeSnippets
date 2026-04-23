async def test_lovelace_from_yaml(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test we load lovelace config from yaml."""
    assert await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "YAML"}})
    assert hass.data[frontend.DATA_PANELS]["lovelace"].config == {"mode": "yaml"}

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config"})
    response = await client.receive_json()
    assert not response["success"]

    assert response["error"]["code"] == "config_not_found"

    # Store new config not allowed
    await client.send_json(
        {"id": 6, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    assert not response["success"]

    # Patch data
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo"},
    ):
        await client.send_json({"id": 7, "type": "lovelace/config"})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo"}

    assert len(events) == 0

    # Fake new data to see we fire event
    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo2"},
    ):
        await client.send_json({"id": 8, "type": "lovelace/config", "force": True})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo2"}

    assert len(events) == 1

    # Make sure when the mtime changes, we reload the config
    with (
        patch(
            "homeassistant.components.lovelace.dashboard.load_yaml_dict",
            return_value={"hello": "yo3"},
        ),
        patch(
            "homeassistant.components.lovelace.dashboard.os.path.getmtime",
            return_value=time.time(),
        ),
    ):
        await client.send_json({"id": 9, "type": "lovelace/config", "force": False})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo3"}

    assert len(events) == 2

    # If the mtime is lower, preserve the cache
    with (
        patch(
            "homeassistant.components.lovelace.dashboard.load_yaml_dict",
            return_value={"hello": "yo4"},
        ),
        patch(
            "homeassistant.components.lovelace.dashboard.os.path.getmtime",
            return_value=0,
        ),
    ):
        await client.send_json({"id": 10, "type": "lovelace/config", "force": False})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo3"}

    assert len(events) == 2