async def test_show_user_form_robot_is_offline_and_locked(hass: HomeAssistant) -> None:
    """Test that the user set up form with config."""

    # Robot not reachable
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(False, False),
    ):
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG_HOST,
        )

        assert result1["errors"].get("host") == "cannot_connect"
        assert result1["step_id"] == "user"
        assert result1["type"] is FlowResultType.FORM

    # Robot is locked
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"], {"host": "1.2.3.4"}
        )

        assert result2["step_id"] == "password"
        assert result2["type"] is FlowResultType.FORM

    # Robot is initialized and unlocked
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {"password": "12345678"}
        )

        assert "errors" not in result3
        assert result3["type"] is FlowResultType.CREATE_ENTRY