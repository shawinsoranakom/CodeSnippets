async def test_reload_moved_automation_without_alias(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test that changing the order of automations without alias triggers reload."""
    with patch(
        "homeassistant.components.automation.AutomationEntity", wraps=AutomationEntity
    ) as automation_entity_init:
        config = {
            automation.DOMAIN: [
                {
                    "triggers": {"platform": "event", "event_type": "test_event"},
                    "actions": [{"action": "test.automation"}],
                },
                {
                    "alias": "automation_with_alias",
                    "triggers": {"platform": "event", "event_type": "test_event2"},
                    "actions": [{"action": "test.automation"}],
                },
            ]
        }
        assert await async_setup_component(hass, automation.DOMAIN, config)
        assert automation_entity_init.call_count == 2
        automation_entity_init.reset_mock()

        assert hass.states.get("automation.automation_0")
        assert not hass.states.get("automation.automation_1")
        assert hass.states.get("automation.automation_with_alias")

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 1

        # Reverse the order of the automations
        config[automation.DOMAIN].reverse()
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )

        assert automation_entity_init.call_count == 1
        automation_entity_init.reset_mock()

        assert not hass.states.get("automation.automation_0")
        assert hass.states.get("automation.automation_1")
        assert hass.states.get("automation.automation_with_alias")

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 2