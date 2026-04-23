async def test_blueprint_script_bad_config(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    blueprint_inputs,
    problem,
    details,
) -> None:
    """Test blueprint script with bad inputs."""
    assert await async_setup_component(
        hass,
        script.DOMAIN,
        {
            script.DOMAIN: {
                "test_script": {
                    "use_blueprint": {
                        "path": "test_service.yaml",
                        "input": blueprint_inputs,
                    }
                }
            }
        },
    )
    assert problem in caplog.text
    assert details in caplog.text

    issues = await get_repairs(hass, hass_ws_client)
    assert len(issues) == 1
    issue = "validation_failed_blueprint"
    assert issues[0]["issue_id"] == f"script.test_script_{issue}"
    assert issues[0]["translation_key"] == issue
    assert issues[0]["translation_placeholders"] == {
        "edit": "/config/script/edit/test_script",
        "entity_id": "script.test_script",
        "error": ANY,
        "name": "test_script",
    }
    assert issues[0]["translation_placeholders"]["error"].startswith(details)