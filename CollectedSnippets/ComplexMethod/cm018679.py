async def test_reauth_flow(
    hass: HomeAssistant, mock_roborock_entry: MockConfigEntry
) -> None:
    """Test reauth flow."""
    result = await mock_roborock_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    # Request a new code
    with (
        patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.request_code_v4"
        ),
        patch("homeassistant.components.roborock.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    # Enter a new code
    assert result["step_id"] == "code"
    assert result["type"] is FlowResultType.FORM
    new_user_data = deepcopy(USER_DATA)
    new_user_data.rriot.s = "new_password_hash"
    with (
        patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.code_login_v4",
            return_value=new_user_data,
        ),
        patch("homeassistant.components.roborock.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ENTRY_CODE: "123456"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_roborock_entry.unique_id == ROBOROCK_RRUID
    assert mock_roborock_entry.data["user_data"]["rriot"]["s"] == "new_password_hash"