async def test_flow_user_init_data_error_and_recover_on_step_2(
    hass: HomeAssistant, raise_error, text_error, user_input
) -> None:
    """Test errors in time mode step."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["handler"] == "swiss_public_transport"
    assert result["data_schema"] == config_flow.USER_DATA_SCHEMA

    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_USER_DATA_STEP_TIME_FIXED,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "time_fixed"

    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        side_effect=raise_error,
    ) as mock_OpendataTransport:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == text_error

        # Recover
        mock_OpendataTransport.side_effect = None
        mock_OpendataTransport.return_value = True
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].title == "test_start test_destination at 18:03:00"