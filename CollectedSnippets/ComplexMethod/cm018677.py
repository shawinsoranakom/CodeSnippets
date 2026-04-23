async def test_config_flow_failures_code_login(
    hass: HomeAssistant,
    code_login_side_effect: Exception | None,
    code_login_errors: dict[str, str],
) -> None:
    """Handle applying errors to code login and recovering from the errors."""
    with patch(
        "homeassistant.components.roborock.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.request_code_v4"
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_USERNAME: USER_EMAIL}
            )

            assert result["type"] is FlowResultType.FORM
            assert result["step_id"] == "code"
            assert result["errors"] == {}
        # Raise exception for invalid code
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.code_login_v4",
            side_effect=code_login_side_effect,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ENTRY_CODE: "123456"}
            )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == code_login_errors
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.code_login_v4",
            return_value=USER_DATA,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ENTRY_CODE: "123456"}
            )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["context"]["unique_id"] == ROBOROCK_RRUID
    assert result["title"] == USER_EMAIL
    assert result["data"] == MOCK_CONFIG
    assert result["result"]
    assert len(mock_setup.mock_calls) == 1