async def test_reload_unchanged_script(
    hass: HomeAssistant, calls: list[ServiceCall], script_config
) -> None:
    """Test an unmodified script is not reloaded."""
    with patch(
        "homeassistant.components.script.ScriptEntity", wraps=ScriptEntity
    ) as script_entity_init:
        config = {script.DOMAIN: [script_config]}
        assert await async_setup_component(hass, script.DOMAIN, config)
        assert hass.states.get(ENTITY_ID) is not None
        assert hass.services.has_service(script.DOMAIN, "test")

        assert script_entity_init.call_count == 1
        script_entity_init.reset_mock()

        # Start the script and wait for it to finish
        _, object_id = split_entity_id(ENTITY_ID)
        await hass.services.async_call(DOMAIN, object_id)
        await hass.async_block_till_done()
        assert len(calls) == 1

        # Reload the scripts without any change
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(script.DOMAIN, SERVICE_RELOAD, blocking=True)

        assert script_entity_init.call_count == 0
        script_entity_init.reset_mock()

        # Start the script and wait for it to start
        _, object_id = split_entity_id(ENTITY_ID)
        await hass.services.async_call(DOMAIN, object_id)
        await hass.async_block_till_done()
        assert len(calls) == 2