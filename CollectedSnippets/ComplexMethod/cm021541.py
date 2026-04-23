async def test_blueprint_template_override(
    hass: HomeAssistant, blueprint: str, override: dict
) -> None:
    """Test blueprint template where the template config overrides the blueprint."""
    assert await async_setup_component(
        hass,
        "template",
        {
            "template": [
                {
                    "use_blueprint": {
                        "path": blueprint,
                        "input": {
                            "event_type": "my_custom_event",
                            "event_data": {"foo": "bar"},
                        },
                    },
                    "name": "My Custom Event",
                }
                | override,
            ]
        },
    )
    await hass.async_block_till_done()

    date_state = hass.states.get("sensor.my_custom_event")
    assert date_state is not None
    assert date_state.state == "unknown"

    context = Context()
    now = dt_util.utcnow()
    with patch("homeassistant.util.dt.now", return_value=now):
        hass.bus.async_fire(
            "my_custom_event", {"foo": "bar", "beer": 2}, context=context
        )
        await hass.async_block_till_done()

    date_state = hass.states.get("sensor.my_custom_event")
    assert date_state is not None
    assert date_state.state == "unknown"

    context = Context()
    now = dt_util.utcnow()
    with patch("homeassistant.util.dt.now", return_value=now):
        hass.bus.async_fire("override", {"foo": "bar", "beer": 2}, context=context)
        await hass.async_block_till_done()

    date_state = hass.states.get("sensor.my_custom_event")
    assert date_state is not None
    assert date_state.state == now.isoformat(timespec="seconds")
    data = date_state.attributes.get("data")
    assert data is not None
    assert data != ""
    assert data.get("foo") == "bar"
    assert data.get("beer") == 2

    inverted_foo_template = template.helpers.blueprint_in_template(
        hass, "sensor.my_custom_event"
    )
    assert inverted_foo_template == blueprint

    inverted_binary_sensor_blueprint_entity_ids = (
        template.helpers.templates_with_blueprint(hass, blueprint)
    )
    assert len(inverted_binary_sensor_blueprint_entity_ids) == 1

    with pytest.raises(BlueprintInUse):
        await template.async_get_blueprints(hass).async_remove_blueprint(blueprint)