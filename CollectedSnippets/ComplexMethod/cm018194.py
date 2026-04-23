async def test_subscribe_conditions(
    mock_has_conditions: Mock,
    mock_load_yaml: Mock,
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
) -> None:
    """Test condition_platforms/subscribe command."""
    sun_condition_descriptions = """
        _: {}
        """
    device_automation_condition_descriptions = """
        _device: {}
        """

    def _load_yaml(fname, secrets=None):
        if fname.endswith("device_automation/conditions.yaml"):
            condition_descriptions = device_automation_condition_descriptions
        elif fname.endswith("sun/conditions.yaml"):
            condition_descriptions = sun_condition_descriptions
        else:
            raise FileNotFoundError
        with io.StringIO(condition_descriptions) as file:
            return parse_yaml(file)

    mock_load_yaml.side_effect = _load_yaml

    assert await async_setup_component(hass, "sun", {})
    assert await async_setup_component(hass, "system_health", {})
    await hass.async_block_till_done()

    assert ALL_CONDITION_DESCRIPTIONS_JSON_CACHE not in hass.data

    await websocket_client.send_json_auto_id({"type": "condition_platforms/subscribe"})

    # Test start subscription with initial event
    msg = await websocket_client.receive_json()
    assert msg == {"id": 1, "result": None, "success": True, "type": "result"}
    msg = await websocket_client.receive_json()
    assert msg == {"event": {"sun": {"fields": {}}}, "id": 1, "type": "event"}

    old_cache = hass.data[ALL_CONDITION_DESCRIPTIONS_JSON_CACHE]

    # Test we receive an event when a new platform is loaded, if it has descriptions
    assert await async_setup_component(hass, "calendar", {})
    assert await async_setup_component(hass, "device_automation", {})
    await hass.async_block_till_done()
    msg = await websocket_client.receive_json()
    assert msg == {
        "event": {"device": {"fields": {}}},
        "id": 1,
        "type": "event",
    }

    # Initiate a second subscription to check the cache is updated because of the new
    # condition
    await websocket_client.send_json_auto_id({"type": "condition_platforms/subscribe"})
    msg = await websocket_client.receive_json()
    assert msg == {"id": 2, "result": None, "success": True, "type": "result"}
    msg = await websocket_client.receive_json()
    assert msg == {
        "event": {"device": {"fields": {}}, "sun": {"fields": {}}},
        "id": 2,
        "type": "event",
    }

    assert hass.data[ALL_CONDITION_DESCRIPTIONS_JSON_CACHE] is not old_cache

    # Initiate a third subscription to check the cache is not updated because no new
    # condition was added
    old_cache = hass.data[ALL_CONDITION_DESCRIPTIONS_JSON_CACHE]
    await websocket_client.send_json_auto_id({"type": "condition_platforms/subscribe"})
    msg = await websocket_client.receive_json()
    assert msg == {"id": 3, "result": None, "success": True, "type": "result"}
    msg = await websocket_client.receive_json()
    assert msg == {
        "event": {"device": {"fields": {}}, "sun": {"fields": {}}},
        "id": 3,
        "type": "event",
    }

    assert hass.data[ALL_CONDITION_DESCRIPTIONS_JSON_CACHE] is old_cache