async def test_reload_template_when_blueprint_changes(hass: HomeAssistant) -> None:
    """Test a template is updated at reload if the blueprint has changed."""
    hass.states.async_set("binary_sensor.foo", "on", {"friendly_name": "Foo"})
    config = {
        DOMAIN: [
            {
                "use_blueprint": {
                    "path": "inverted_binary_sensor.yaml",
                    "input": {"reference_entity": "binary_sensor.foo"},
                },
                "name": "Inverted foo",
            },
        ]
    }
    with patch_blueprint(
        "inverted_binary_sensor.yaml",
        BUILTIN_BLUEPRINT_FOLDER / "inverted_binary_sensor.yaml",
    ):
        assert await async_setup_component(hass, DOMAIN, config)

    hass.states.async_set("binary_sensor.foo", "off", {"friendly_name": "Foo"})
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.foo").state == "off"

    inverted = hass.states.get("binary_sensor.inverted_foo")
    assert inverted
    assert inverted.state == "on"

    # Reload the automations without any change, but with updated blueprint
    blueprint_config = yaml_util.load_yaml(
        BUILTIN_BLUEPRINT_FOLDER / "inverted_binary_sensor.yaml"
    )
    blueprint_config["binary_sensor"]["state"] = "{{ states(reference_entity) }}"
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

    hass.states.async_set("binary_sensor.foo", "off", {"friendly_name": "Foo"})
    await hass.async_block_till_done()

    not_inverted = hass.states.get("binary_sensor.inverted_foo")
    assert not_inverted
    assert not_inverted.state == "off"

    hass.states.async_set("binary_sensor.foo", "on", {"friendly_name": "Foo"})
    await hass.async_block_till_done()

    not_inverted = hass.states.get("binary_sensor.inverted_foo")
    assert not_inverted
    assert not_inverted.state == "on"