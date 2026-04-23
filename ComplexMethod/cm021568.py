async def test_reload_config_handles_load_fails(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test the reload config service."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "action": "test.automation",
                    "data_template": {"event": "{{ trigger.event.event_type }}"},
                },
            }
        },
    )
    assert hass.states.get("automation.hello") is not None

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data.get("event") == "test_event"

    with (
        patch(
            "homeassistant.config.load_yaml_config_file",
            side_effect=HomeAssistantError("bla"),
        ),
        pytest.raises(
            ServiceValidationError, match="Failed to load configuration: bla"
        ),
    ):
        await hass.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)

    assert hass.states.get("automation.hello") is not None

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 2

    with (
        patch(
            "homeassistant.config.load_yaml_config_file",
        ),
        patch(
            "homeassistant.config.async_process_component_and_handle_errors",
            side_effect=ConfigValidationError(
                "config_schema_unknown_err",
                [Exception("bla")],
                translation_domain="homeassistant",
                translation_placeholders={"domain": "bla", "error": "bla"},
            ),
        ),
        pytest.raises(
            ServiceValidationError,
            match="Unknown error calling bla CONFIG_SCHEMA - bla",
        ) as exc_info,
    ):
        await hass.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)
    assert exc_info.value.translation_domain == "homeassistant"
    assert exc_info.value.translation_key == "config_schema_unknown_err"
    assert exc_info.value.translation_placeholders == {"domain": "bla", "error": "bla"}

    assert hass.states.get("automation.hello") is not None

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 3