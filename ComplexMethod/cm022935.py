async def test_bad_config_validation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    hass_admin_user: MockUser,
    object_id,
    broken_config,
    problem,
    details,
    issue,
) -> None:
    """Test bad script configuration which can be detected during validation."""
    assert await async_setup_component(
        hass,
        script.DOMAIN,
        {
            script.DOMAIN: {
                object_id: {"alias": "bad_script", **broken_config},
                "good_script": {
                    "alias": "good_script",
                    "sequence": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                },
            }
        },
    )

    # Check we get the expected error message and issue
    assert (
        f"Script with alias 'bad_script' {problem} and has been disabled: {details}"
        in caplog.text
    )
    issues = await get_repairs(hass, hass_ws_client)
    assert len(issues) == 1
    assert issues[0]["issue_id"] == f"script.bad_script_{issue}"
    assert issues[0]["translation_key"] == issue
    assert issues[0]["translation_placeholders"] == {
        "edit": "/config/script/edit/bad_script",
        "entity_id": "script.bad_script",
        "error": ANY,
        "name": "bad_script",
    }
    assert issues[0]["translation_placeholders"]["error"].startswith(details)

    # Make sure both scripts are setup
    assert set(hass.states.async_entity_ids("script")) == {
        "script.bad_script",
        "script.good_script",
    }
    # The script failing validation should be unavailable
    assert hass.states.get("script.bad_script").state == STATE_UNAVAILABLE

    # Reloading the automation with fixed config should clear the issue
    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            script.DOMAIN: {
                object_id: {
                    "alias": "bad_script",
                    "sequence": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                },
            }
        },
    ):
        await hass.services.async_call(
            script.DOMAIN,
            SERVICE_RELOAD,
            context=Context(user_id=hass_admin_user.id),
            blocking=True,
        )
    issues = await get_repairs(hass, hass_ws_client)
    assert len(issues) == 0