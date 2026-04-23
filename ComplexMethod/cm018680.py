async def test_account_already_configured(
    hass: HomeAssistant,
    mock_roborock_entry: MockConfigEntry,
) -> None:
    """Ensure the same account cannot be setup twice."""
    assert mock_roborock_entry.unique_id == ROBOROCK_RRUID
    with patch(
        "homeassistant.components.roborock.async_setup_entry", return_value=True
    ):
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

        assert result["step_id"] == "code"
        assert result["type"] is FlowResultType.FORM
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.code_login_v4",
            return_value=USER_DATA,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ENTRY_CODE: "123456"}
            )
            assert result["type"] is FlowResultType.ABORT
            assert result["reason"] == "already_configured_account"