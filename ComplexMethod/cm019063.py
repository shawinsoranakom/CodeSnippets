async def test_show_user_form_robot_unlock_with_password(hass: HomeAssistant) -> None:
    """Test that the user set up form with config."""

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG_HOST,
        )

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "12345678"}
        )

        assert result2["errors"] == {"password": "invalid_auth"}
        assert result2["step_id"] == "password"
        assert result2["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(False, False),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {"password": "12345678"}
        )

        assert result3["errors"] == {"password": "cannot_connect"}
        assert result3["step_id"] == "password"
        assert result3["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"], {"password": "12345678"}
        )

        assert "errors" not in result4
        assert result4["type"] is FlowResultType.CREATE_ENTRY