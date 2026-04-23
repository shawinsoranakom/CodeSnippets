async def test_render_template_manual_entity_ids_no_longer_needed(
    hass: HomeAssistant, websocket_client
) -> None:
    """Test that updates to specified entity ids cause a template rerender."""
    hass.states.async_set("light.test", "on")

    await websocket_client.send_json_auto_id(
        {
            "type": "render_template",
            "template": "State is: {{ states('light.test') }}",
        }
    )

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "State is: on",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["light.test"],
            "time": False,
        },
    }

    hass.states.async_set("light.test", "off")
    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "State is: off",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["light.test"],
            "time": False,
        },
    }