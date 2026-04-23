async def test_reload_identical_automations_without_id(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test reloading of identical automations without id."""
    with patch(
        "homeassistant.components.automation.AutomationEntity", wraps=AutomationEntity
    ) as automation_entity_init:
        config = {
            automation.DOMAIN: [
                {
                    "alias": "dolly",
                    "triggers": {"platform": "event", "event_type": "test_event"},
                    "actions": [{"action": "test.automation"}],
                },
                {
                    "alias": "dolly",
                    "triggers": {"platform": "event", "event_type": "test_event"},
                    "actions": [{"action": "test.automation"}],
                },
                {
                    "alias": "dolly",
                    "triggers": {"platform": "event", "event_type": "test_event"},
                    "actions": [{"action": "test.automation"}],
                },
            ]
        }
        assert await async_setup_component(hass, automation.DOMAIN, config)
        assert automation_entity_init.call_count == 3
        automation_entity_init.reset_mock()

        assert hass.states.get("automation.dolly")
        assert hass.states.get("automation.dolly_2")
        assert hass.states.get("automation.dolly_3")

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 3

        # Reload the automations without any change
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )

        assert automation_entity_init.call_count == 0
        automation_entity_init.reset_mock()

        assert hass.states.get("automation.dolly")
        assert hass.states.get("automation.dolly_2")
        assert hass.states.get("automation.dolly_3")

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 6

        # Remove two clones
        del config[automation.DOMAIN][-1]
        del config[automation.DOMAIN][-1]
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )

        assert automation_entity_init.call_count == 0
        automation_entity_init.reset_mock()

        assert hass.states.get("automation.dolly")

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 7

        # Add two clones
        config[automation.DOMAIN].append(config[automation.DOMAIN][-1])
        config[automation.DOMAIN].append(config[automation.DOMAIN][-1])
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )

        assert automation_entity_init.call_count == 2
        automation_entity_init.reset_mock()

        assert hass.states.get("automation.dolly")
        assert hass.states.get("automation.dolly_2")
        assert hass.states.get("automation.dolly_3")

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 10