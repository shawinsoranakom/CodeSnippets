async def test_automation_bad_config_validation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    hass_admin_user: MockUser,
    broken_config: dict[str, Any],
    problem: str,
    details: str,
    issue: str,
) -> None:
    """Test bad automation configuration which can be detected during validation."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {"alias": "bad_automation", **broken_config},
                {
                    "alias": "good_automation",
                    "triggers": {"platform": "event", "event_type": "test_event"},
                    "actions": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                },
            ]
        },
    )

    # Check we get the expected error message and issue
    assert (
        f"Automation with alias 'bad_automation' {problem} and has been disabled:"
        f" {details}"
    ) in caplog.text
    issues = await get_repairs(hass, hass_ws_client)
    assert len(issues) == 1
    assert issues[0]["issue_id"] == f"automation.bad_automation_{issue}"
    assert issues[0]["translation_key"] == issue
    assert issues[0]["translation_placeholders"] == {
        "edit": "/config/automation/edit/None",
        "entity_id": "automation.bad_automation",
        "error": ANY,
        "name": "bad_automation",
    }
    assert issues[0]["translation_placeholders"]["error"].startswith(details)

    # Make sure both automations are setup
    assert set(hass.states.async_entity_ids("automation")) == {
        "automation.bad_automation",
        "automation.good_automation",
    }
    # The automation failing validation should be unavailable
    assert hass.states.get("automation.bad_automation").state == STATE_UNAVAILABLE

    # Reloading the automation with fixed config should clear the issue
    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            automation.DOMAIN: {
                "alias": "bad_automation",
                "trigger": {"platform": "event", "event_type": "test_event2"},
                "action": {
                    "action": "test.automation",
                    "data_template": {"event": "{{ trigger.event.event_type }}"},
                },
            }
        },
    ):
        await hass.services.async_call(
            automation.DOMAIN,
            SERVICE_RELOAD,
            context=Context(user_id=hass_admin_user.id),
            blocking=True,
        )
    issues = await get_repairs(hass, hass_ws_client)
    assert len(issues) == 0