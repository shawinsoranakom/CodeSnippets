async def test_init_attribute_variables_from_blueprint(hass: HomeAssistant) -> None:
    """Test a state based blueprint initializes icon, name, and picture with variables."""
    blueprint = "test_init_attribute_variables.yaml"
    source = "switch.foo"
    entity_id = "sensor.foo"
    hass.states.async_set(source, "on", {"friendly_name": "Foo"})
    config = {
        DOMAIN: [
            {
                "use_blueprint": {
                    "path": blueprint,
                    "input": {"switch": source},
                },
            }
        ],
    }
    assert await async_setup_component(
        hass,
        DOMAIN,
        config,
    )
    await hass.async_block_till_done()

    # Check initial state
    sensor = hass.states.get(entity_id)
    assert sensor
    assert sensor.state == "True"
    assert sensor.attributes["icon"] == "mdi:lightbulb"
    assert sensor.attributes["entity_picture"] == "on.png"
    assert sensor.attributes["friendly_name"] == "Foo"
    assert sensor.attributes["extra"] == "ab"

    hass.states.async_set(source, "off", {"friendly_name": "Foo"})
    await hass.async_block_till_done()

    # Check to see that the template light works
    sensor = hass.states.get(entity_id)
    assert sensor
    assert sensor.state == "False"
    assert sensor.attributes["icon"] == "mdi:lightbulb-off"
    assert sensor.attributes["entity_picture"] == "off.png"
    assert sensor.attributes["friendly_name"] == "Foo"
    assert sensor.attributes["extra"] == "ab"

    # Reload the templates without any change, but with updated blueprint
    blueprint_config = yaml_util.load_yaml(
        pathlib.Path("tests/testing_config/blueprints/template/") / blueprint
    )
    blueprint_config["variables"]["extraa"] = "c"
    blueprint_config["sensor"]["variables"]["extrab"] = "d"
    with (
        patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ),
        patch(
            "homeassistant.components.blueprint.models.yaml_util.load_yaml_dict",
            autospec=True,
            return_value=blueprint_config,
        ),
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    sensor = hass.states.get(entity_id)
    assert sensor
    assert sensor.state == "False"
    assert sensor.attributes["icon"] == "mdi:lightbulb-off"
    assert sensor.attributes["entity_picture"] == "off.png"
    assert sensor.attributes["friendly_name"] == "Foo"
    assert sensor.attributes["extra"] == "cd"

    hass.states.async_set(source, "on", {"friendly_name": "Foo"})
    await hass.async_block_till_done()

    sensor = hass.states.get(entity_id)
    assert sensor
    assert sensor.state == "True"
    assert sensor.attributes["icon"] == "mdi:lightbulb"
    assert sensor.attributes["entity_picture"] == "on.png"
    assert sensor.attributes["friendly_name"] == "Foo"
    assert sensor.attributes["extra"] == "cd"