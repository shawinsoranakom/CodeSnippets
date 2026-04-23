async def test_inverted_binary_sensor(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test inverted binary sensor blueprint."""
    hass.states.async_set("binary_sensor.foo", "on", {"friendly_name": "Foo"})
    hass.states.async_set("binary_sensor.bar", "off", {"friendly_name": "Bar"})

    with patch_blueprint(
        "inverted_binary_sensor.yaml",
        BUILTIN_BLUEPRINT_FOLDER / "inverted_binary_sensor.yaml",
    ):
        assert await async_setup_component(
            hass,
            "template",
            {
                "template": [
                    {
                        "use_blueprint": {
                            "path": "inverted_binary_sensor.yaml",
                            "input": {"reference_entity": "binary_sensor.foo"},
                        },
                        "name": "Inverted foo",
                    },
                    {
                        "use_blueprint": {
                            "path": "inverted_binary_sensor.yaml",
                            "input": {"reference_entity": "binary_sensor.bar"},
                        },
                        "name": "Inverted bar",
                    },
                ]
            },
        )

    hass.states.async_set("binary_sensor.foo", "off", {"friendly_name": "Foo"})
    hass.states.async_set("binary_sensor.bar", "on", {"friendly_name": "Bar"})
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.foo").state == "off"
    assert hass.states.get("binary_sensor.bar").state == "on"

    inverted_foo = hass.states.get("binary_sensor.inverted_foo")
    assert inverted_foo
    assert inverted_foo.state == "on"

    inverted_bar = hass.states.get("binary_sensor.inverted_bar")
    assert inverted_bar
    assert inverted_bar.state == "off"

    foo_template = template.helpers.blueprint_in_template(hass, "binary_sensor.foo")
    inverted_foo_template = template.helpers.blueprint_in_template(
        hass, "binary_sensor.inverted_foo"
    )
    assert foo_template is None
    assert inverted_foo_template == "inverted_binary_sensor.yaml"

    inverted_binary_sensor_blueprint_entity_ids = (
        template.helpers.templates_with_blueprint(hass, "inverted_binary_sensor.yaml")
    )
    assert len(inverted_binary_sensor_blueprint_entity_ids) == 2

    assert len(template.helpers.templates_with_blueprint(hass, "dummy.yaml")) == 0

    with pytest.raises(BlueprintInUse):
        await template.async_get_blueprints(hass).async_remove_blueprint(
            "inverted_binary_sensor.yaml"
        )