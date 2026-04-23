async def test_flow_user_init_data_success(
    hass: HomeAssistant, user_input, time_mode_input, config_title
) -> None:
    """Test success response."""
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
            user_input=user_input,
        )

        if time_mode_input:
            assert result["type"] is FlowResultType.FORM
            if CONF_TIME_FIXED in time_mode_input:
                assert result["step_id"] == "time_fixed"
            if CONF_TIME_OFFSET in time_mode_input:
                assert result["step_id"] == "time_offset"
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input=time_mode_input,
            )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].title == config_title

        assert result["data"] == {**user_input, **(time_mode_input or {})}