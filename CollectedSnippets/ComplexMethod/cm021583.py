async def test_blueprint_automation_bad_config(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    blueprint_inputs,
    problem,
    details,
) -> None:
    """Test blueprint automation with bad inputs."""
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "use_blueprint": {
                    "path": "test_event_service.yaml",
                    "input": blueprint_inputs,
                }
            }
        },
    )
    assert problem in caplog.text
    assert details in caplog.text

    issues = await get_repairs(hass, hass_ws_client)
    assert len(issues) == 1
    issue = "validation_failed_blueprint"
    assert issues[0]["issue_id"] == f"automation.automation_0_{issue}"
    assert issues[0]["translation_key"] == issue
    assert issues[0]["translation_placeholders"] == {
        "edit": "/config/automation/edit/None",
        "entity_id": "automation.automation_0",
        "error": ANY,
        "name": "automation 0",
    }
    assert issues[0]["translation_placeholders"]["error"].startswith(details)