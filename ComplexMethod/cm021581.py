async def test_automation_variables(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test automation variables."""
    calls = async_mock_service(hass, "test", "automation")

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "variables": {
                        "test_var": "defined_in_config",
                        "event_type": "{{ trigger.event.event_type }}",
                        "this_variables": "{{this.entity_id}}",
                    },
                    "triggers": {"trigger": "event", "event_type": "test_event"},
                    "actions": {
                        "action": "test.automation",
                        "data": {
                            "value": "{{ test_var }}",
                            "event_type": "{{ event_type }}",
                            "this_template": "{{this.entity_id}}",
                            "this_variables": "{{this_variables}}",
                        },
                    },
                },
                {
                    "variables": {
                        "test_var": "defined_in_config",
                    },
                    "trigger": {"trigger": "event", "event_type": "test_event_2"},
                    "conditions": {
                        "condition": "template",
                        "value_template": "{{ trigger.event.data.pass_condition }}",
                    },
                    "actions": {
                        "action": "test.automation",
                    },
                },
                {
                    "variables": {
                        "test_var": "{{ trigger.event.data.break + 1 }}",
                    },
                    "triggers": {"trigger": "event", "event_type": "test_event_3"},
                    "actions": {
                        "action": "test.automation",
                    },
                },
            ]
        },
    )
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["value"] == "defined_in_config"
    assert calls[0].data["event_type"] == "test_event"
    # Verify this available to all templates
    assert calls[0].data.get("this_template") == "automation.automation_0"
    # Verify this available during variables rendering
    assert calls[0].data.get("this_variables") == "automation.automation_0"
    assert "Error rendering variables" not in caplog.text

    hass.bus.async_fire("test_event_2")
    await hass.async_block_till_done()
    assert len(calls) == 1

    hass.bus.async_fire("test_event_2", {"pass_condition": True})
    await hass.async_block_till_done()
    assert len(calls) == 2

    assert "Error rendering variables" not in caplog.text
    hass.bus.async_fire("test_event_3")
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert "Error rendering variables" in caplog.text

    hass.bus.async_fire("test_event_3", {"break": 0})
    await hass.async_block_till_done()
    assert len(calls) == 3