async def test_subscribe_triggers(
    mock_has_triggers: Mock,
    mock_load_yaml: Mock,
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
) -> None:
    """Test trigger_platforms/subscribe command."""
    sun_trigger_descriptions = """
        _: {}
        """
    tag_trigger_descriptions = """
        _: {}
        """

    def _load_yaml(fname, secrets=None):
        if fname.endswith("sun/triggers.yaml"):
            trigger_descriptions = sun_trigger_descriptions
        elif fname.endswith("tag/triggers.yaml"):
            trigger_descriptions = tag_trigger_descriptions
        else:
            raise FileNotFoundError
        with io.StringIO(trigger_descriptions) as file:
            return parse_yaml(file)

    mock_load_yaml.side_effect = _load_yaml

    assert await async_setup_component(hass, "sun", {})
    assert await async_setup_component(hass, "system_health", {})
    await hass.async_block_till_done()

    assert ALL_TRIGGER_DESCRIPTIONS_JSON_CACHE not in hass.data

    await websocket_client.send_json_auto_id({"type": "trigger_platforms/subscribe"})

    # Test start subscription with initial event
    msg = await websocket_client.receive_json()
    assert msg == {"id": 1, "result": None, "success": True, "type": "result"}
    msg = await websocket_client.receive_json()
    assert msg == {"event": {"sun": {"fields": {}}}, "id": 1, "type": "event"}

    old_cache = hass.data[ALL_TRIGGER_DESCRIPTIONS_JSON_CACHE]

    # Test we receive an event when a new platform is loaded, if it has descriptions
    assert await async_setup_component(hass, "calendar", {})
    assert await async_setup_component(hass, "tag", {})
    await hass.async_block_till_done()
    msg = await websocket_client.receive_json()
    assert msg == {
        "event": {"tag": {"fields": {}}},
        "id": 1,
        "type": "event",
    }

    # Initiate a second subscription to check the cache is updated because of the new
    # trigger
    await websocket_client.send_json_auto_id({"type": "trigger_platforms/subscribe"})
    msg = await websocket_client.receive_json()
    assert msg == {"id": 2, "result": None, "success": True, "type": "result"}
    msg = await websocket_client.receive_json()
    assert msg == {
        "event": {"sun": {"fields": {}}, "tag": {"fields": {}}},
        "id": 2,
        "type": "event",
    }

    assert hass.data[ALL_TRIGGER_DESCRIPTIONS_JSON_CACHE] is not old_cache

    # Initiate a third subscription to check the cache is not updated because no new
    # trigger was added
    old_cache = hass.data[ALL_TRIGGER_DESCRIPTIONS_JSON_CACHE]
    await websocket_client.send_json_auto_id({"type": "trigger_platforms/subscribe"})
    msg = await websocket_client.receive_json()
    assert msg == {"id": 3, "result": None, "success": True, "type": "result"}
    msg = await websocket_client.receive_json()
    assert msg == {
        "event": {"sun": {"fields": {}}, "tag": {"fields": {}}},
        "id": 3,
        "type": "event",
    }

    assert hass.data[ALL_TRIGGER_DESCRIPTIONS_JSON_CACHE] is old_cache