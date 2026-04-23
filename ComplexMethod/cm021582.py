async def test_automation_trigger_variables(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test automation trigger variables."""
    calls = async_mock_service(hass, "test", "automation")

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "variables": {
                        "event_type": "{{ trigger.event.event_type }}",
                    },
                    "trigger_variables": {
                        "test_var": "defined_in_config",
                    },
                    "trigger": {"trigger": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "data": {
                            "value": "{{ test_var }}",
                            "event_type": "{{ event_type }}",
                        },
                    },
                },
                {
                    "variables": {
                        "event_type": "{{ trigger.event.event_type }}",
                        "test_var": "overridden_in_config",
                    },
                    "trigger_variables": {
                        "test_var": "defined_in_config",
                        "this_trigger_variables": "{{this.entity_id}}",
                    },
                    "trigger": {"trigger": "event", "event_type": "test_event_2"},
                    "action": {
                        "action": "test.automation",
                        "data": {
                            "value": "{{ test_var }}",
                            "event_type": "{{ event_type }}",
                            "this_template": "{{this.entity_id}}",
                            "this_trigger_variables": "{{this_trigger_variables}}",
                        },
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

    hass.bus.async_fire("test_event_2")
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["value"] == "overridden_in_config"
    assert calls[1].data["event_type"] == "test_event_2"
    # Verify this available to all templates
    assert calls[1].data.get("this_template") == "automation.automation_1"
    # Verify this available during trigger variables rendering
    assert calls[1].data.get("this_trigger_variables") == "automation.automation_1"
    assert "Error rendering variables" not in caplog.text